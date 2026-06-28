use crate::db::Database;
use crate::licensing;
use crate::AppState;
use chrono::Utc;
use rusqlite::{params, OptionalExtension};
use serde::{Deserialize, Serialize};
use std::path::Path;
use tauri::State;
use uuid::Uuid;

const AGENT_JONATHAN: &str = "jonathan";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiProviderRecord {
    pub id: String,
    pub name: String,
    pub provider_type: String,
    pub base_url: String,
    pub enabled: bool,
    pub api_key_configured: bool,
    pub health_status: String,
    pub health_message: Option<String>,
    pub last_health_check_at: Option<String>,
    pub allowed_roles: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiAgentRecord {
    pub id: String,
    pub agent_key: String,
    pub name: String,
    pub provider_id: Option<String>,
    pub model: String,
    pub enabled: bool,
    pub allowed_roles: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiOrgPolicy {
    pub cloud_ai_enabled: bool,
    pub default_provider_id: Option<String>,
    pub monthly_budget_usd: f64,
    pub monthly_token_limit: i64,
    pub enforce_budget: bool,
    pub updated_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiUsageSummary {
    pub month: String,
    pub total_tokens: i64,
    pub prompt_tokens: i64,
    pub completion_tokens: i64,
    pub estimated_cost_usd: f64,
    pub request_count: i64,
    pub budget_used_percent: f64,
    pub token_limit_used_percent: f64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiAuditEntry {
    pub id: String,
    pub action: String,
    pub actor: String,
    pub details: String,
    pub created_at: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct EnterpriseAiDashboard {
    pub providers: Vec<AiProviderRecord>,
    pub agents: Vec<AiAgentRecord>,
    pub policy: AiOrgPolicy,
    pub usage: AiUsageSummary,
    pub audit_log: Vec<AiAuditEntry>,
    pub roles: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct UpsertAiProviderRequest {
    pub id: Option<String>,
    pub name: String,
    pub provider_type: String,
    pub base_url: String,
    pub enabled: bool,
    pub api_key: Option<String>,
    pub allowed_roles: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct RotateProviderKeyRequest {
    pub provider_id: String,
    pub api_key: String,
}

#[derive(Debug, Clone, Deserialize)]
pub struct UpsertAiAgentRequest {
    pub agent_key: String,
    pub name: String,
    pub provider_id: Option<String>,
    pub model: String,
    pub enabled: bool,
    pub allowed_roles: Vec<String>,
}

#[derive(Debug, Clone, Deserialize)]
pub struct UpdateAiOrgPolicyRequest {
    pub cloud_ai_enabled: bool,
    pub default_provider_id: Option<String>,
    pub monthly_budget_usd: f64,
    pub monthly_token_limit: i64,
    pub enforce_budget: bool,
}

#[derive(Debug, Clone, Serialize)]
pub struct ProviderHealthResult {
    pub provider_id: String,
    pub status: String,
    pub message: String,
    pub checked_at: String,
}

#[derive(Debug, Clone)]
pub struct ResolvedAiRuntime {
    pub provider_id: String,
    pub provider_type: String,
    pub base_url: String,
    pub model: String,
    pub api_key: String,
}

fn require_console(db: &Database) -> Result<(), String> {
    licensing::require_feature(db, "enterprise_ai_console")
}

fn actor_name(db: &Database) -> String {
    db.get_profile()
        .map(|p| p.display_name)
        .unwrap_or_else(|_| "admin".to_string())
}

fn audit(db: &Database, action: &str, details: &str) -> Result<(), String> {
    db.conn()
        .execute(
            "INSERT INTO ai_audit_log (id, action, actor, details, created_at) VALUES (?1, ?2, ?3, ?4, ?5)",
            params![
                Uuid::new_v4().to_string(),
                action,
                actor_name(db),
                details,
                Utc::now().to_rfc3339()
            ],
        )
        .map_err(|e| e.to_string())?;
    Ok(())
}

fn ensure_defaults(db: &Database) -> Result<(), String> {
    let count: i64 = db
        .conn()
        .query_row("SELECT COUNT(*) FROM ai_providers", [], |r| r.get(0))
        .map_err(|e| e.to_string())?;
    if count > 0 {
        return Ok(());
    }

    let now = Utc::now().to_rfc3339();
    let openai_id = "openai-default".to_string();
    let anthropic_id = "anthropic-default".to_string();

    for (id, name, ptype, url) in [
        (&openai_id, "OpenAI", "openai", "https://api.openai.com/v1"),
        (
            &anthropic_id,
            "Anthropic",
            "anthropic",
            "https://api.anthropic.com/v1",
        ),
    ] {
        db.conn()
            .execute(
                "INSERT INTO ai_providers (id, name, provider_type, base_url, enabled, health_status, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, 1, 'unknown', ?5, ?5)",
                params![id, name, ptype, url, now],
            )
            .map_err(|e| e.to_string())?;
        for role in ["admin", "technician", "user"] {
            db.conn()
                .execute(
                    "INSERT INTO ai_provider_role_access (provider_id, role, allowed) VALUES (?1, ?2, 1)",
                    params![id, role],
                )
                .map_err(|e| e.to_string())?;
        }
    }

    db.conn()
        .execute(
            "INSERT INTO ai_agents (id, agent_key, name, provider_id, model, enabled, allowed_roles, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, 1, ?6, ?7, ?7)",
            params![
                Uuid::new_v4().to_string(),
                AGENT_JONATHAN,
                "Jonathan",
                openai_id,
                "gpt-4o-mini",
                r#"["admin","technician","user"]"#,
                now
            ],
        )
        .map_err(|e| e.to_string())?;

    db.conn()
        .execute(
            "UPDATE ai_org_policy SET default_provider_id = ?1, updated_at = ?2 WHERE id = 1",
            params![openai_id, now],
        )
        .map_err(|e| e.to_string())?;

    Ok(())
}

fn provider_allowed_roles(db: &Database, provider_id: &str) -> Result<Vec<String>, String> {
    let mut stmt = db
        .conn()
        .prepare("SELECT role FROM ai_provider_role_access WHERE provider_id = ?1 AND allowed = 1")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map(params![provider_id], |row| row.get(0))
        .map_err(|e| e.to_string())?;
    rows.collect::<Result<Vec<String>, _>>()
        .map_err(|e| e.to_string())
}

fn load_providers(db: &Database, data_dir: &Path) -> Result<Vec<AiProviderRecord>, String> {
    let mut stmt = db
        .conn()
        .prepare(
            "SELECT id, name, provider_type, base_url, enabled, health_status, health_message, last_health_check_at FROM ai_providers ORDER BY name",
        )
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok((
                row.get::<_, String>(0)?,
                row.get::<_, String>(1)?,
                row.get::<_, String>(2)?,
                row.get::<_, String>(3)?,
                row.get::<_, i64>(4)? == 1,
                row.get::<_, String>(5)?,
                row.get::<_, Option<String>>(6)?,
                row.get::<_, Option<String>>(7)?,
            ))
        })
        .map_err(|e| e.to_string())?;

    let mut providers = Vec::new();
    for row in rows {
        let (id, name, provider_type, base_url, enabled, health_status, health_message, last_health_check_at) =
            row.map_err(|e| e.to_string())?;
        let api_key_configured = crate::secrets::get_provider_api_key(data_dir, &id)?
            .map(|k| !k.is_empty())
            .unwrap_or(false);
        let allowed_roles = provider_allowed_roles(db, &id)?;
        providers.push(AiProviderRecord {
            id,
            name,
            provider_type,
            base_url,
            enabled,
            api_key_configured,
            health_status,
            health_message,
            last_health_check_at,
            allowed_roles,
        });
    }
    Ok(providers)
}

fn load_agents(db: &Database) -> Result<Vec<AiAgentRecord>, String> {
    let mut stmt = db
        .conn()
        .prepare("SELECT id, agent_key, name, provider_id, model, enabled, allowed_roles FROM ai_agents ORDER BY name")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map([], |row| {
            Ok(AiAgentRecord {
                id: row.get(0)?,
                agent_key: row.get(1)?,
                name: row.get(2)?,
                provider_id: row.get(3)?,
                model: row.get(4)?,
                enabled: row.get::<_, i64>(5)? == 1,
                allowed_roles: serde_json::from_str(&row.get::<_, String>(6)?).unwrap_or_default(),
            })
        })
        .map_err(|e| e.to_string())?;
    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())
}

fn load_policy(db: &Database) -> Result<AiOrgPolicy, String> {
    db.conn()
        .query_row(
            "SELECT cloud_ai_enabled, default_provider_id, monthly_budget_usd, monthly_token_limit, enforce_budget, updated_at FROM ai_org_policy WHERE id = 1",
            [],
            |row| {
                Ok(AiOrgPolicy {
                    cloud_ai_enabled: row.get::<_, i64>(0)? == 1,
                    default_provider_id: row.get(1)?,
                    monthly_budget_usd: row.get(2)?,
                    monthly_token_limit: row.get(3)?,
                    enforce_budget: row.get::<_, i64>(4)? == 1,
                    updated_at: row.get(5)?,
                })
            },
        )
        .map_err(|e| e.to_string())
}

fn load_usage_summary(db: &Database, policy: &AiOrgPolicy) -> Result<AiUsageSummary, String> {
    let month_prefix = Utc::now().format("%Y-%m").to_string();
    let (prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd, request_count): (
        i64,
        i64,
        i64,
        f64,
        i64,
    ) = db
        .conn()
        .query_row(
            "SELECT COALESCE(SUM(prompt_tokens),0), COALESCE(SUM(completion_tokens),0), COALESCE(SUM(total_tokens),0), COALESCE(SUM(estimated_cost_usd),0), COUNT(*) FROM ai_usage_log WHERE created_at LIKE ?1",
            params![format!("{month_prefix}%")],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?, row.get(4)?)),
        )
        .map_err(|e| e.to_string())?;

    let budget_used_percent = if policy.monthly_budget_usd > 0.0 {
        (estimated_cost_usd / policy.monthly_budget_usd * 100.0).min(100.0)
    } else {
        0.0
    };
    let token_limit_used_percent = if policy.monthly_token_limit > 0 {
        (total_tokens as f64 / policy.monthly_token_limit as f64 * 100.0).min(100.0)
    } else {
        0.0
    };

    Ok(AiUsageSummary {
        month: month_prefix,
        total_tokens,
        prompt_tokens,
        completion_tokens,
        estimated_cost_usd,
        request_count,
        budget_used_percent,
        token_limit_used_percent,
    })
}

fn load_audit_log(db: &Database, limit: i64) -> Result<Vec<AiAuditEntry>, String> {
    let mut stmt = db
        .conn()
        .prepare("SELECT id, action, actor, details, created_at FROM ai_audit_log ORDER BY created_at DESC LIMIT ?1")
        .map_err(|e| e.to_string())?;
    let rows = stmt
        .query_map(params![limit], |row| {
            Ok(AiAuditEntry {
                id: row.get(0)?,
                action: row.get(1)?,
                actor: row.get(2)?,
                details: row.get(3)?,
                created_at: row.get(4)?,
            })
        })
        .map_err(|e| e.to_string())?;
    rows.collect::<Result<Vec<_>, _>>()
        .map_err(|e| e.to_string())
}

pub fn estimate_cost_usd(model: &str, prompt_tokens: i64, completion_tokens: i64) -> f64 {
    let (input_rate, output_rate) = if model.contains("gpt-4o-mini") {
        (0.15, 0.60)
    } else if model.contains("gpt-4o") {
        (2.50, 10.0)
    } else if model.contains("claude") {
        (3.0, 15.0)
    } else {
        (1.0, 3.0)
    };
    (prompt_tokens as f64 / 1_000_000.0) * input_rate
        + (completion_tokens as f64 / 1_000_000.0) * output_rate
}

pub fn log_ai_usage(
    db: &Database,
    agent_key: &str,
    provider_id: Option<&str>,
    model: &str,
    prompt_tokens: i64,
    completion_tokens: i64,
) -> Result<(), String> {
    let total = prompt_tokens + completion_tokens;
    let cost = estimate_cost_usd(model, prompt_tokens, completion_tokens);
    db.conn()
        .execute(
            "INSERT INTO ai_usage_log (id, agent_key, provider_id, model, prompt_tokens, completion_tokens, total_tokens, estimated_cost_usd, created_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?9)",
            params![
                Uuid::new_v4().to_string(),
                agent_key,
                provider_id,
                model,
                prompt_tokens,
                completion_tokens,
                total,
                cost,
                Utc::now().to_rfc3339()
            ],
        )
        .map_err(|e| e.to_string())?;
    Ok(())
}

pub fn resolve_runtime(
    db: &Database,
    data_dir: &Path,
    agent_key: &str,
) -> Result<Option<ResolvedAiRuntime>, String> {
    if !licensing::has_feature(db, "enterprise_ai_console").unwrap_or(false) {
        return Ok(None);
    }

    let policy = load_policy(db)?;
    if !policy.cloud_ai_enabled {
        return Err("Cloud AI is disabled by your organization policy.".to_string());
    }

    let profile = db.get_profile().map_err(|e| e.to_string())?;
    let usage = load_usage_summary(db, &policy)?;
    if policy.enforce_budget {
        if usage.estimated_cost_usd >= policy.monthly_budget_usd {
            return Err("Monthly AI budget limit reached. Contact your administrator.".to_string());
        }
        if usage.total_tokens >= policy.monthly_token_limit {
            return Err("Monthly AI token limit reached. Contact your administrator.".to_string());
        }
    }

    let agent: (Option<String>, String, i64, String) = db
        .conn()
        .query_row(
            "SELECT provider_id, model, enabled, allowed_roles FROM ai_agents WHERE agent_key = ?1",
            params![agent_key],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?, row.get(3)?)),
        )
        .optional()
        .map_err(|e| e.to_string())?
        .ok_or_else(|| format!("AI agent '{agent_key}' is not configured."))?;

    if agent.2 != 1 {
        return Err(format!("AI agent '{agent_key}' is disabled by policy."));
    }

    let allowed_roles: Vec<String> = serde_json::from_str(&agent.3).unwrap_or_default();
    if !allowed_roles.iter().any(|r| r == &profile.role) {
        return Err(format!(
            "Your role '{}' is not permitted to use agent '{}'.",
            profile.role, agent_key
        ));
    }

    let provider_id = agent
        .0
        .or(policy.default_provider_id.clone())
        .ok_or_else(|| "No AI provider configured for this agent.".to_string())?;

    let provider: (String, String, i64) = db
        .conn()
        .query_row(
            "SELECT provider_type, base_url, enabled FROM ai_providers WHERE id = ?1",
            params![provider_id],
            |row| Ok((row.get(0)?, row.get(1)?, row.get(2)?)),
        )
        .map_err(|_| "Configured AI provider was not found.".to_string())?;

    if provider.2 != 1 {
        return Err("The configured AI provider is disabled.".to_string());
    }

    let role_allowed: i64 = db
        .conn()
        .query_row(
            "SELECT allowed FROM ai_provider_role_access WHERE provider_id = ?1 AND role = ?2",
            params![provider_id, profile.role],
            |row| row.get(0),
        )
        .unwrap_or(0);
    if role_allowed != 1 {
        return Err(format!(
            "Your role '{}' cannot use provider '{}'.",
            profile.role, provider_id
        ));
    }

    let api_key = crate::secrets::get_provider_api_key(data_dir, &provider_id)?
        .filter(|k| !k.is_empty())
        .ok_or_else(|| "AI provider API key is not configured.".to_string())?;

    Ok(Some(ResolvedAiRuntime {
        provider_id,
        provider_type: provider.0,
        base_url: provider.1,
        model: agent.1,
        api_key,
    }))
}

async fn test_provider_connection(
    provider_type: &str,
    base_url: &str,
    api_key: &str,
) -> Result<String, String> {
    let client = reqwest::Client::new();
    let url = if provider_type == "anthropic" {
        format!("{}/models", base_url.trim_end_matches('/'))
    } else {
        format!("{}/models", base_url.trim_end_matches('/'))
    };

    let mut req = client.get(url);
    if provider_type == "anthropic" {
        req = req.header("x-api-key", api_key).header("anthropic-version", "2023-06-01");
    } else {
        req = req.header("Authorization", format!("Bearer {api_key}"));
    }

    let response = req
        .send()
        .await
        .map_err(|e| format!("Connection failed: {e}"))?;

    if response.status().is_success() {
        Ok("Connection successful.".to_string())
    } else {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        Err(format!("HTTP {status}: {body}"))
    }
}

#[tauri::command]
pub async fn get_enterprise_ai_dashboard(state: State<'_, AppState>) -> Result<EnterpriseAiDashboard, String> {
    let db = state.lock_db()?;
    require_console(&db)?;
    ensure_defaults(&db)?;

    let policy = load_policy(&db)?;
    let usage = load_usage_summary(&db, &policy)?;

    Ok(EnterpriseAiDashboard {
        providers: load_providers(&db, &state.data_dir)?,
        agents: load_agents(&db)?,
        policy,
        usage,
        audit_log: load_audit_log(&db, 50)?,
        roles: vec![
            "admin".into(),
            "technician".into(),
            "user".into(),
        ],
    })
}

#[tauri::command]
pub fn upsert_ai_provider(
    state: State<AppState>,
    request: UpsertAiProviderRequest,
) -> Result<AiProviderRecord, String> {
    let db = state.lock_db()?;
    require_console(&db)?;

    let id = request.id.unwrap_or_else(|| Uuid::new_v4().to_string());
    let now = Utc::now().to_rfc3339();
    let exists: bool = db
        .conn()
        .query_row(
            "SELECT COUNT(*) FROM ai_providers WHERE id = ?1",
            params![id],
            |row| row.get(0),
        )
        .map_err(|e| e.to_string())?;

    if exists {
        db.conn()
            .execute(
                "UPDATE ai_providers SET name = ?1, provider_type = ?2, base_url = ?3, enabled = ?4, updated_at = ?5 WHERE id = ?6",
                params![request.name, request.provider_type, request.base_url, request.enabled as i64, now, id],
            )
            .map_err(|e| e.to_string())?;
        audit(&db, "provider.updated", &format!("Updated provider {}", request.name))?;
    } else {
        db.conn()
            .execute(
                "INSERT INTO ai_providers (id, name, provider_type, base_url, enabled, health_status, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, 'unknown', ?6, ?6)",
                params![id, request.name, request.provider_type, request.base_url, request.enabled as i64, now],
            )
            .map_err(|e| e.to_string())?;
        audit(&db, "provider.created", &format!("Created provider {}", request.name))?;
    }

    if let Some(key) = request.api_key {
        if !key.trim().is_empty() {
            crate::secrets::store_provider_api_key(&state.data_dir, &id, &key)?;
            audit(&db, "provider.key_rotated", &format!("Rotated API key for {}", request.name))?;
        }
    }

    db.conn()
        .execute(
            "DELETE FROM ai_provider_role_access WHERE provider_id = ?1",
            params![id],
        )
        .map_err(|e| e.to_string())?;
    for role in request.allowed_roles {
        db.conn()
            .execute(
                "INSERT INTO ai_provider_role_access (provider_id, role, allowed) VALUES (?1, ?2, 1)",
                params![id, role],
            )
            .map_err(|e| e.to_string())?;
    }

    load_providers(&db, &state.data_dir)?
        .into_iter()
        .find(|p| p.id == id)
        .ok_or_else(|| "Provider not found after save.".to_string())
}

#[tauri::command]
pub fn rotate_provider_api_key(
    state: State<AppState>,
    request: RotateProviderKeyRequest,
) -> Result<(), String> {
    let db = state.lock_db()?;
    require_console(&db)?;
    crate::secrets::store_provider_api_key(&state.data_dir, &request.provider_id, &request.api_key)?;
    audit(
        &db,
        "provider.key_rotated",
        &format!("Rotated API key for provider {}", request.provider_id),
    )?;
    Ok(())
}

#[tauri::command]
pub fn upsert_ai_agent(state: State<AppState>, request: UpsertAiAgentRequest) -> Result<AiAgentRecord, String> {
    let db = state.lock_db()?;
    require_console(&db)?;
    let now = Utc::now().to_rfc3339();
    let roles_json = serde_json::to_string(&request.allowed_roles).map_err(|e| e.to_string())?;

    let existing: Option<String> = db
        .conn()
        .query_row(
            "SELECT id FROM ai_agents WHERE agent_key = ?1",
            params![request.agent_key],
            |row| row.get(0),
        )
        .optional()
        .map_err(|e| e.to_string())?;

    if let Some(id) = existing {
        db.conn()
            .execute(
                "UPDATE ai_agents SET name = ?1, provider_id = ?2, model = ?3, enabled = ?4, allowed_roles = ?5, updated_at = ?6 WHERE id = ?7",
                params![request.name, request.provider_id, request.model, request.enabled as i64, roles_json, now, id],
            )
            .map_err(|e| e.to_string())?;
    } else {
        db.conn()
            .execute(
                "INSERT INTO ai_agents (id, agent_key, name, provider_id, model, enabled, allowed_roles, created_at, updated_at) VALUES (?1, ?2, ?3, ?4, ?5, ?6, ?7, ?8, ?8)",
                params![Uuid::new_v4().to_string(), request.agent_key, request.name, request.provider_id, request.model, request.enabled as i64, roles_json, now],
            )
            .map_err(|e| e.to_string())?;
    }

    audit(
        &db,
        "agent.updated",
        &format!("Updated agent {} model {}", request.name, request.model),
    )?;

    load_agents(&db)?
        .into_iter()
        .find(|a| a.agent_key == request.agent_key)
        .ok_or_else(|| "Agent not found after save.".to_string())
}

#[tauri::command]
pub fn update_ai_org_policy(state: State<AppState>, request: UpdateAiOrgPolicyRequest) -> Result<AiOrgPolicy, String> {
    let db = state.lock_db()?;
    require_console(&db)?;
    let now = Utc::now().to_rfc3339();
    db.conn()
        .execute(
            "UPDATE ai_org_policy SET cloud_ai_enabled = ?1, default_provider_id = ?2, monthly_budget_usd = ?3, monthly_token_limit = ?4, enforce_budget = ?5, updated_at = ?6 WHERE id = 1",
            params![
                request.cloud_ai_enabled as i64,
                request.default_provider_id,
                request.monthly_budget_usd,
                request.monthly_token_limit,
                request.enforce_budget as i64,
                now
            ],
        )
        .map_err(|e| e.to_string())?;
    audit(&db, "policy.updated", "Updated organization AI policy")?;
    load_policy(&db)
}

#[tauri::command]
pub async fn test_ai_provider_health(
    state: State<'_, AppState>,
    provider_id: String,
) -> Result<ProviderHealthResult, String> {
    let (provider_type, base_url, api_key) = {
        let db = state.lock_db()?;
        require_console(&db)?;

        let provider: (String, String) = db
            .conn()
            .query_row(
                "SELECT provider_type, base_url FROM ai_providers WHERE id = ?1",
                params![provider_id],
                |row| Ok((row.get(0)?, row.get(1)?)),
            )
            .map_err(|_| "Provider not found.".to_string())?;

        let api_key = crate::secrets::get_provider_api_key(&state.data_dir, &provider_id)?
            .ok_or_else(|| "No API key configured for this provider.".to_string())?;

        (provider.0, provider.1, api_key)
    };

    let checked_at = Utc::now().to_rfc3339();
    let (status, message) = match test_provider_connection(&provider_type, &base_url, &api_key).await {
        Ok(msg) => ("healthy".to_string(), msg),
        Err(err) => ("unhealthy".to_string(), err),
    };

    let db = state.lock_db()?;
    db.conn()
        .execute(
            "UPDATE ai_providers SET health_status = ?1, health_message = ?2, last_health_check_at = ?3, updated_at = ?3 WHERE id = ?4",
            params![status, message, checked_at, provider_id],
        )
        .map_err(|e| e.to_string())?;

    audit(
        &db,
        "provider.health_check",
        &format!("Health check for {provider_id}: {status}"),
    )?;

    Ok(ProviderHealthResult {
        provider_id,
        status,
        message,
        checked_at,
    })
}

#[tauri::command]
pub fn list_ai_audit_log(state: State<AppState>, limit: Option<i64>) -> Result<Vec<AiAuditEntry>, String> {
    let db = state.lock_db()?;
    require_console(&db)?;
    load_audit_log(&db, limit.unwrap_or(100))
}
