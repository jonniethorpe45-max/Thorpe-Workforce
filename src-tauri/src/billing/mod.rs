use serde::{Deserialize, Serialize};

const DEFAULT_BILLING_PATH: &str = "/checkout";

fn validate_service_url(url: &str) -> Result<(), String> {
    if cfg!(debug_assertions) {
        let parsed = url::Url::parse(url.trim()).map_err(|_| "Invalid URL format.".to_string())?;
        if parsed.scheme() == "http" {
            if let Some(host) = parsed.host_str() {
                if host == "localhost" || host == "127.0.0.1" {
                    return Ok(());
                }
            }
        }
    }
    crate::net::validate_https_url(url, false)
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct BillingConfig {
    pub billing_api_url: Option<String>,
    pub stripe_configured: bool,
    pub license_api_url: Option<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CheckoutSession {
    pub session_id: String,
    pub checkout_url: String,
    pub stripe_configured: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct CheckoutStatus {
    pub session_id: String,
    pub status: String,
    pub tier: Option<String>,
    pub license_key: Option<String>,
}

fn billing_api_base() -> Option<String> {
    std::env::var("THORPE_BILLING_API_URL")
        .ok()
        .filter(|value| !value.trim().is_empty())
        .map(|value| value.trim().trim_end_matches('/').to_string())
}

fn license_api_url() -> Option<String> {
    std::env::var("THORPE_LICENSE_API_URL")
        .ok()
        .filter(|value| !value.trim().is_empty())
        .map(|value| value.trim().to_string())
}

#[tauri::command]
pub async fn get_billing_config() -> Result<BillingConfig, String> {
    let billing_api_url = billing_api_base();
    let stripe_configured = if let Some(base) = &billing_api_url {
        check_stripe_configured(base).await.unwrap_or(false)
    } else {
        false
    };

    Ok(BillingConfig {
        billing_api_url,
        stripe_configured,
        license_api_url: license_api_url(),
    })
}

async fn check_stripe_configured(base: &str) -> Result<bool, String> {
    let health_url = format!("{base}/health");
    validate_service_url(&health_url)?;

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(10))
        .build()
        .map_err(|e| e.to_string())?;

    let response = client.get(&health_url).send().await.map_err(|e| e.to_string())?;
    if !response.status().is_success() {
        return Ok(false);
    }

    let body: serde_json::Value = response.json().await.map_err(|e| e.to_string())?;
    Ok(body
        .get("stripe_configured")
        .and_then(|value| value.as_bool())
        .unwrap_or(false))
}

#[derive(Serialize)]
struct CreateCheckoutRequest<'a> {
    tier: &'a str,
    #[serde(skip_serializing_if = "Option::is_none")]
    customer_email: Option<&'a str>,
}

#[tauri::command]
pub async fn create_billing_checkout(
    tier: String,
    customer_email: Option<String>,
) -> Result<CheckoutSession, String> {
    let base = billing_api_base().ok_or_else(|| {
        "Billing is not configured. Set THORPE_BILLING_API_URL to your license server base URL.".to_string()
    })?;

    let checkout_url = format!("{base}{DEFAULT_BILLING_PATH}");
    validate_service_url(&checkout_url)?;

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(20))
        .build()
        .map_err(|e| e.to_string())?;

    let body = CreateCheckoutRequest {
        tier: tier.as_str(),
        customer_email: customer_email.as_deref(),
    };

    let response = client
        .post(&checkout_url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("Billing server unreachable: {e}"))?;

    if !response.status().is_success() {
        let status = response.status();
        let message = response.text().await.unwrap_or_default();
        return Err(format!(
            "Checkout failed (HTTP {status}){}",
            if message.is_empty() {
                ".".to_string()
            } else {
                format!(": {message}")
            }
        ));
    }

    let payload: serde_json::Value = response.json().await.map_err(|e| e.to_string())?;
    let session_id = payload
        .get("session_id")
        .and_then(|value| value.as_str())
        .ok_or_else(|| "Billing server did not return session_id".to_string())?
        .to_string();
    let checkout_url = payload
        .get("checkout_url")
        .and_then(|value| value.as_str())
        .ok_or_else(|| "Billing server did not return checkout_url".to_string())?
        .to_string();

    Ok(CheckoutSession {
        session_id,
        checkout_url,
        stripe_configured: payload
            .get("stripe_configured")
            .and_then(|value| value.as_bool())
            .unwrap_or(true),
    })
}

#[tauri::command]
pub async fn get_checkout_status(session_id: String) -> Result<CheckoutStatus, String> {
    let base = billing_api_base().ok_or_else(|| {
        "Billing is not configured. Set THORPE_BILLING_API_URL to your license server base URL.".to_string()
    })?;

    let status_url = format!("{base}/checkout/{session_id}/status");
    validate_service_url(&status_url)?;

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(15))
        .build()
        .map_err(|e| e.to_string())?;

    let response = client
        .get(&status_url)
        .send()
        .await
        .map_err(|e| format!("Billing status check failed: {e}"))?;

    if response.status() == reqwest::StatusCode::NOT_FOUND {
        return Ok(CheckoutStatus {
            session_id,
            status: "pending".to_string(),
            tier: None,
            license_key: None,
        });
    }

    if !response.status().is_success() {
        let status = response.status();
        let message = response.text().await.unwrap_or_default();
        return Err(format!(
            "Billing status failed (HTTP {status}){}",
            if message.is_empty() {
                ".".to_string()
            } else {
                format!(": {message}")
            }
        ));
    }

    let payload: serde_json::Value = response.json().await.map_err(|e| e.to_string())?;
    Ok(CheckoutStatus {
        session_id: payload
            .get("session_id")
            .and_then(|value| value.as_str())
            .unwrap_or(&session_id)
            .to_string(),
        status: payload
            .get("status")
            .and_then(|value| value.as_str())
            .unwrap_or("pending")
            .to_string(),
        tier: payload
            .get("tier")
            .and_then(|value| value.as_str())
            .map(str::to_string),
        license_key: payload
            .get("license_key")
            .and_then(|value| value.as_str())
            .map(str::to_string),
    })
}

#[tauri::command]
pub async fn open_external_url(app: tauri::AppHandle, url: String) -> Result<(), String> {
    crate::net::validate_https_url(&url, false)?;
    use tauri_plugin_opener::OpenerExt;
    app.opener()
        .open_url(url, None::<&str>)
        .map_err(|e| e.to_string())?;
    Ok(())
}
