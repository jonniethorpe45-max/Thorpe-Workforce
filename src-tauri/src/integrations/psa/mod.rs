use crate::db::{AgentSessionRecord, SupportCase};
use crate::secrets;
use crate::AppState;
use hmac::{Hmac, Mac};
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::json;
use sha2::Sha256;
use std::path::PathBuf;
use tauri::State;

type HmacSha256 = Hmac<Sha256>;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PsaConfig {
    pub enabled: bool,
    pub webhook_url: Option<String>,
    pub provider: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PsaDeliveryResult {
    pub success: bool,
    pub status_code: Option<u16>,
    pub message: String,
}

#[derive(Clone)]
struct PsaDeliveryContext {
    config: PsaConfig,
    data_dir: PathBuf,
}

pub fn get_psa_config(state: &State<'_, AppState>) -> Result<PsaConfig, String> {
    let db = state.lock_db()?;
    Ok(PsaConfig {
        enabled: db
            .get_setting("psa_enabled")
            .ok()
            .flatten()
            .map(|v| v == "true")
            .unwrap_or(false),
        webhook_url: db.get_setting("psa_webhook_url").ok().flatten(),
        provider: db
            .get_setting("psa_provider")
            .ok()
            .flatten()
            .unwrap_or_else(|| "generic".to_string()),
    })
}

pub fn save_psa_config(
    state: &State<'_, AppState>,
    enabled: bool,
    webhook_url: Option<String>,
    provider: String,
    secret: Option<String>,
) -> Result<PsaConfig, String> {
    let db = state.lock_db()?;
    db.set_setting("psa_enabled", if enabled { "true" } else { "false" })
        .map_err(|e| e.to_string())?;
    match &webhook_url {
        Some(url) if url.trim().is_empty() => {
            let _ = db.delete_setting("psa_webhook_url");
        }
        Some(url) => {
            crate::net::validate_https_url(url, true)?;
            db.set_setting("psa_webhook_url", url.trim()).map_err(|e| e.to_string())?;
        }
        None => {
            let _ = db.delete_setting("psa_webhook_url");
        }
    }
    db.set_setting("psa_provider", &provider)
        .map_err(|e| e.to_string())?;
    if let Some(sec) = secret {
        if !sec.trim().is_empty() {
            secrets::store_psa_secret(&state.data_dir, &sec)?;
        }
    }
    get_psa_config(state)
}

fn delivery_context(state: &State<'_, AppState>) -> Result<Option<PsaDeliveryContext>, String> {
    let config = get_psa_config(state)?;
    if !config.enabled {
        return Ok(None);
    }
    Ok(Some(PsaDeliveryContext {
        config,
        data_dir: state.data_dir.clone(),
    }))
}

pub fn spawn_case_event(state: &State<'_, AppState>, event: &'static str, case: SupportCase) {
    let Ok(Some(ctx)) = delivery_context(state) else {
        return;
    };
    tauri::async_runtime::spawn(async move {
        let _ = deliver_webhook(
            &ctx,
            event,
            json!({
                "event": event,
                "provider": ctx.config.provider,
                "case": case,
                "timestamp": chrono::Utc::now().to_rfc3339(),
            }),
            None,
        )
        .await;
    });
}

pub fn spawn_agent_session(state: &State<'_, AppState>, session: AgentSessionRecord) {
    let Ok(Some(ctx)) = delivery_context(state) else {
        return;
    };
    tauri::async_runtime::spawn(async move {
        let _ = deliver_webhook(
            &ctx,
            "agent.session.completed",
            json!({
                "event": "agent.session.completed",
                "provider": ctx.config.provider,
                "session": session,
                "timestamp": chrono::Utc::now().to_rfc3339(),
            }),
            None,
        )
        .await;
    });
}

async fn deliver_webhook(
    ctx: &PsaDeliveryContext,
    event: &str,
    payload: serde_json::Value,
    secret_override: Option<&str>,
) -> Result<PsaDeliveryResult, String> {
    let url = ctx
        .config
        .webhook_url
        .as_ref()
        .filter(|u| !u.is_empty())
        .ok_or_else(|| "PSA webhook URL is not configured.".to_string())?;
    crate::net::validate_https_url(url, true)?;

    let body = serde_json::to_string(&payload).map_err(|e| e.to_string())?;
    let mut req = Client::new()
        .post(url)
        .header("Content-Type", "application/json")
        .header("X-Thorpe-Event", event)
        .header("User-Agent", "Thorpe-Desktop/1.1");

    let secret = secret_override
        .map(|s| s.to_string())
        .or_else(|| secrets::get_psa_secret(&ctx.data_dir).ok().flatten());

    if let Some(secret) = secret.filter(|s| !s.is_empty()) {
        let mut mac = HmacSha256::new_from_slice(secret.as_bytes()).map_err(|e| e.to_string())?;
        mac.update(body.as_bytes());
        let sig = hex::encode(mac.finalize().into_bytes());
        req = req.header("X-Thorpe-Signature", format!("sha256={sig}"));
    }

    let response = req
        .body(body)
        .send()
        .await
        .map_err(|e| format!("PSA webhook failed: {e}"))?;

    let status = response.status();
    Ok(PsaDeliveryResult {
        success: status.is_success(),
        status_code: Some(status.as_u16()),
        message: if status.is_success() {
            "Delivered to PSA webhook.".to_string()
        } else {
            format!("PSA webhook returned HTTP {}", status)
        },
    })
}

#[tauri::command]
pub fn get_psa_settings(state: State<AppState>) -> Result<PsaConfig, String> {
    get_psa_config(&state)
}

#[tauri::command]
pub fn update_psa_settings(
    state: State<AppState>,
    enabled: bool,
    webhook_url: Option<String>,
    provider: String,
    secret: Option<String>,
) -> Result<PsaConfig, String> {
    save_psa_config(&state, enabled, webhook_url, provider, secret)
}

#[tauri::command]
pub async fn test_psa_webhook(
    state: State<'_, AppState>,
    webhook_url: Option<String>,
    secret: Option<String>,
) -> Result<PsaDeliveryResult, String> {
    let payload = json!({
        "event": "test.ping",
        "message": "Thorpe PSA webhook test",
        "timestamp": chrono::Utc::now().to_rfc3339(),
    });

    if let Some(url) = webhook_url.filter(|u| !u.trim().is_empty()) {
        crate::net::validate_https_url(url.trim(), true)?;
        let ctx = PsaDeliveryContext {
            config: PsaConfig {
                enabled: true,
                webhook_url: Some(url.trim().to_string()),
                provider: "generic".to_string(),
            },
            data_dir: state.data_dir.clone(),
        };
        return deliver_webhook(&ctx, "test.ping", payload, secret.as_deref()).await;
    }

    let ctx = delivery_context(&state)?.ok_or_else(|| "PSA integration is disabled.".to_string())?;
    deliver_webhook(&ctx, "test.ping", payload, secret.as_deref()).await
}
