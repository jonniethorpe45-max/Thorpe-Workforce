use serde::{Deserialize, Serialize};

#[derive(Debug, Deserialize)]
pub struct OnlineLicenseResponse {
    pub tier: String,
    pub expires_at: Option<String>,
    pub organization: Option<String>,
}

#[derive(Serialize)]
struct ActivateRequest<'a> {
    license_key: &'a str,
    #[serde(skip_serializing_if = "Option::is_none")]
    organization: Option<&'a str>,
    app_version: &'a str,
    platform: &'a str,
}

pub async fn activate_license_online(
    api_url: &str,
    license_key: &str,
    organization: Option<&str>,
) -> Result<OnlineLicenseResponse, String> {
    crate::net::validate_https_url(api_url, false)?;

    let client = reqwest::Client::builder()
        .timeout(std::time::Duration::from_secs(20))
        .build()
        .map_err(|e| e.to_string())?;

    let body = ActivateRequest {
        license_key,
        organization,
        app_version: env!("CARGO_PKG_VERSION"),
        platform: std::env::consts::OS,
    };

    let response = client
        .post(api_url)
        .json(&body)
        .send()
        .await
        .map_err(|e| format!("License server unreachable: {e}"))?;

    if !response.status().is_success() {
        let status = response.status();
        let message = response.text().await.unwrap_or_default();
        return Err(format!(
            "License activation failed (HTTP {status}){}",
            if message.is_empty() {
                ".".to_string()
            } else {
                format!(": {message}")
            }
        ));
    }

    response
        .json::<OnlineLicenseResponse>()
        .await
        .map_err(|e| format!("Invalid license server response: {e}"))
}
