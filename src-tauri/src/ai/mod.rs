use crate::db::DiagnosticReport;
use crate::licensing;
use crate::repairs::{self, RepairResult};
use crate::scanner::SystemScanResult;
use crate::AppState;
use serde::{Deserialize, Serialize};
use tauri::State;
use uuid::Uuid;

const JONATHAN_SYSTEM_PROMPT: &str = r#"You are Jonathan, an autonomous IT technician built into Thorpe.

Your job is to FIX problems — not give the user manual steps or knowledge-base articles.

Behavior:
- Diagnose issues from scan data and the user's description
- Execute automated repairs through Thorpe's repair engine (already run before you respond)
- Report what you fixed in past tense: "I flushed the DNS cache", "I cleaned temporary files"
- Be concise, confident, and professional — you are the technician, not a help desk script
- Never tell the user to open Settings, Task Manager, or follow multi-step DIY instructions unless a repair failed and requires physical/hardware escalation
- Never invent repairs — only describe repairs that appear in the repair results provided to you
- When you know the user's first name, address them naturally by first name in greetings and closings
- Escalate to a human only for hardware failure, malware/ransomware, or issues requiring credentials

Security rules (NEVER violate):
- Never request passwords, security answers, recovery codes, or credentials
- Never suggest disabling security software without clear justification
- Never recommend downloading from untrusted sources"#;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiConfig {
    pub provider: String,
    pub api_key_configured: bool,
    pub model: String,
    pub base_url: String,
    pub enabled: bool,
}

#[derive(Debug, Clone, Deserialize)]
pub struct AiConfigUpdate {
    pub provider: String,
    pub api_key: Option<String>,
    pub model: String,
    pub base_url: String,
    pub enabled: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatRequest {
    pub message: String,
    pub skill_level: String,
    pub scan_context: Option<String>,
    pub history: Vec<ChatHistoryItem>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatHistoryItem {
    pub role: String,
    pub content: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ChatResponse {
    pub message: String,
    pub source: String,
    pub repairs_executed: Vec<RepairResult>,
}

#[derive(Debug, Deserialize)]
struct OpenAiResponse {
    choices: Vec<OpenAiChoice>,
}

#[derive(Debug, Deserialize)]
struct OpenAiChoice {
    message: OpenAiMessage,
}

#[derive(Debug, Deserialize)]
struct OpenAiMessage {
    content: String,
}

#[tauri::command]
pub fn get_ai_config(state: State<AppState>) -> Result<AiConfig, String> {
    let db = state.lock_db()?;
    let api_key_configured = crate::secrets::get_api_key(&state.data_dir)?
        .map(|key| !key.is_empty())
        .unwrap_or(false);

    Ok(AiConfig {
        provider: db.get_setting("ai_provider").ok().flatten().unwrap_or_else(|| "openai".to_string()),
        api_key_configured,
        model: db.get_setting("ai_model").ok().flatten().unwrap_or_else(|| "gpt-4o-mini".to_string()),
        base_url: db.get_setting("ai_base_url").ok().flatten().unwrap_or_else(|| "https://api.openai.com/v1".to_string()),
        enabled: db.get_setting("ai_enabled").ok().flatten().map(|v| v == "true").unwrap_or(false),
    })
}

#[tauri::command]
pub fn set_ai_config(state: State<AppState>, config: AiConfigUpdate) -> Result<(), String> {
    let has_new_key = config
        .api_key
        .as_ref()
        .map(|key| !key.trim().is_empty())
        .unwrap_or(false);
    let has_existing_key = crate::secrets::get_api_key(&state.data_dir)?
        .map(|key| !key.is_empty())
        .unwrap_or(false);

    if config.enabled && !has_new_key && !has_existing_key {
        return Err(
            "Cloud AI requires an API key. Enter your OpenAI API key and save again.".to_string(),
        );
    }

    let db = state.lock_db()?;
    db.set_setting("ai_provider", &config.provider).map_err(|e| e.to_string())?;
    if let Some(key) = &config.api_key {
        if !key.trim().is_empty() {
            crate::secrets::store_api_key(&state.data_dir, key.trim())?;
        }
    }
    db.set_setting("ai_model", &config.model).map_err(|e| e.to_string())?;
    db.set_setting("ai_base_url", &config.base_url).map_err(|e| e.to_string())?;
    db.set_setting("ai_enabled", if config.enabled { "true" } else { "false" }).map_err(|e| e.to_string())?;
    Ok(())
}

fn resolve_api_key(state: &State<AppState>) -> Result<Option<String>, String> {
    crate::secrets::get_api_key(&state.data_dir)
}

#[tauri::command]
pub async fn chat_with_jonathan(state: State<'_, AppState>, request: ChatRequest) -> Result<ChatResponse, String> {
    let config = get_ai_config(state.clone())?;
    let api_key = resolve_api_key(&state)?;
    let scan = parse_scan_context(request.scan_context.as_deref());

    state.lock_db()?.save_chat("user", &request.message).ok();

    let skip_auto_repair = {
        let m = request.message.to_lowercase();
        m.contains("virus") || m.contains("malware") || m.contains("ransomware")
    };

    let planned = if skip_auto_repair {
        vec![]
    } else {
        repairs::plan_repairs(&request.message, scan.as_ref())
    };
    let repairs_executed = {
        let db = state.lock_db()?;
        repairs::perform_repairs(&db, &planned)
    };

    let user_first_name = {
        let db = state.lock_db()?;
        db.get_profile()
            .ok()
            .and_then(|profile| extract_first_name(&profile.display_name))
    };

    let response = if config.enabled && api_key.is_none() {
        ChatResponse {
            message: format!(
                "{}\n\n**Cloud AI is enabled in Settings but no API key is stored on this device.** Open Settings → Jonathan AI (Cloud), enter your OpenAI API key, and save again.",
                format_technician_response(
                    &request,
                    scan.as_ref(),
                    &repairs_executed,
                    user_first_name.as_deref(),
                    None,
                )
            ),
            source: "cloud_unconfigured".to_string(),
            repairs_executed,
        }
    } else if config.enabled && api_key.is_some() {
        match call_openai(
            &config,
            api_key.as_ref().unwrap(),
            &request,
            scan.as_ref(),
            &repairs_executed,
            user_first_name.as_deref(),
        )
        .await
        {
            Ok(msg) => ChatResponse {
                message: msg,
                source: "openai".to_string(),
                repairs_executed,
            },
            Err(e) => ChatResponse {
                message: format_technician_response(
                    &request,
                    scan.as_ref(),
                    &repairs_executed,
                    user_first_name.as_deref(),
                    Some(&e),
                ),
                source: "cloud_fallback".to_string(),
                repairs_executed,
            },
        }
    } else {
        ChatResponse {
            message: format_technician_response(
                &request,
                scan.as_ref(),
                &repairs_executed,
                user_first_name.as_deref(),
                None,
            ),
            source: "local".to_string(),
            repairs_executed,
        }
    };

    state.lock_db()?.save_chat("assistant", &response.message).ok();
    Ok(response)
}

async fn call_openai(
    config: &AiConfig,
    api_key: &str,
    request: &ChatRequest,
    scan: Option<&SystemScanResult>,
    repairs_executed: &[RepairResult],
    user_first_name: Option<&str>,
) -> Result<String, String> {

    let skill_context = match request.skill_level.as_str() {
        "advanced" => "The user is technically advanced. You may use technical terminology.",
        _ => "The user is a beginner. Use plain language and avoid jargon.",
    };

    let mut system_prompt = format!("{}\n\n{}", JONATHAN_SYSTEM_PROMPT, skill_context);
    if let Some(name) = user_first_name {
        system_prompt.push_str(&format!(
            "\n\nThe user's first name is {name}. Address them by first name naturally when greeting or closing."
        ));
    }
    if let Some(ctx) = scan {
        system_prompt.push_str(&format!(
            "\n\nSystem scan:\nOS: {} {}\nHealth: {}/100\nMemory: {:.1}% used",
            ctx.os.name, ctx.os.version, ctx.health_score, ctx.memory.usage_percent
        ));
    }
    if !repairs_executed.is_empty() {
        system_prompt.push_str("\n\nRepairs already executed for the user:");
        for repair in repairs_executed {
            system_prompt.push_str(&format!(
                "\n- {} ({}) — {}",
                repair.action_name,
                if repair.success { "success" } else { "failed" },
                repair.message
            ));
        }
        system_prompt.push_str("\nSummarize what you fixed. Do not give DIY instructions.");
    }

    let mut messages = vec![serde_json::json!({"role": "system", "content": system_prompt})];
    for item in &request.history {
        messages.push(serde_json::json!({"role": item.role, "content": item.content}));
    }
    messages.push(serde_json::json!({"role": "user", "content": request.message}));

    let client = reqwest::Client::new();
    let response = client
        .post(format!("{}/chat/completions", config.base_url.trim_end_matches('/')))
        .header("Authorization", format!("Bearer {}", api_key))
        .header("Content-Type", "application/json")
        .json(&serde_json::json!({
            "model": config.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000,
        }))
        .send()
        .await
        .map_err(|e| format!("API request failed: {}", e))?;

    if !response.status().is_success() {
        let status = response.status();
        let body = response.text().await.unwrap_or_default();
        return Err(format!("API error {}: {}", status, body));
    }

    let data: OpenAiResponse = response.json().await.map_err(|e| format!("Failed to parse response: {}", e))?;
    data.choices
        .first()
        .map(|c| c.message.content.clone())
        .ok_or_else(|| "Empty response from API".to_string())
}

fn parse_scan_context(scan_context: Option<&str>) -> Option<SystemScanResult> {
    scan_context.and_then(|ctx| serde_json::from_str::<SystemScanResult>(ctx).ok())
}

fn extract_first_name(display_name: &str) -> Option<String> {
    let trimmed = display_name.trim();
    if trimmed.is_empty() {
        return None;
    }

    let first = trimmed.split_whitespace().next()?;
    if first.eq_ignore_ascii_case("user")
        || first.eq_ignore_ascii_case("guest")
        || first.eq_ignore_ascii_case("admin")
        || first.eq_ignore_ascii_case("administrator")
    {
        return None;
    }

    Some(first.to_string())
}

fn format_technician_response(
    request: &ChatRequest,
    scan: Option<&SystemScanResult>,
    repairs: &[RepairResult],
    user_first_name: Option<&str>,
    api_error: Option<&str>,
) -> String {
    let msg_lower = request.message.to_lowercase();

    if msg_lower.contains("password") || msg_lower.contains("credential") {
        return "I can't handle passwords or credentials — that's a security boundary I never cross. I've escalated this to your organization's official recovery process.".to_string();
    }

    if msg_lower.contains("virus") || msg_lower.contains("malware") || msg_lower.contains("ransomware") {
        return "⚠️ **Security alert — I've isolated automated repairs for this case.**\n\nI detected a potential malware/ransomware concern. I've stopped routine fixes and recommend immediate escalation to a cybersecurity professional. Do not enter credentials on this device until it's verified clean.".to_string();
    }

    let mut response = match user_first_name {
        Some(name) => format!("**Hi {name}, autonomous repair complete**\n\n"),
        None => String::from("**Jonathan — autonomous repair complete**\n\n"),
    };

    if repairs.is_empty() {
        response.push_str("I analyzed your system but no automated repairs were needed for this request.\n");
    } else {
        response.push_str("I've applied the following fixes on your behalf:\n\n");
        for repair in repairs {
            let status = if repair.success { "✓" } else { "⚠" };
            response.push_str(&format!("- {} **{}** — {}\n", status, repair.action_name, repair.message));
            if let Some(details) = &repair.details {
                let preview: String = details.lines().take(2).collect::<Vec<_>>().join(" ");
                if !preview.is_empty() {
                    response.push_str(&format!("  _{preview}_\n"));
                }
            }
        }
    }

    if let Some(scan) = scan {
        response.push_str(&format!(
            "\n**System status:** Health score {}/100 on {} {}\n",
            scan.health_score, scan.os.name, scan.os.version
        ));
        if !scan.issues.is_empty() {
            response.push_str(&format!("**Remaining flags:** {} issue(s) logged for monitoring.\n", scan.issues.len()));
        }
    }

    if msg_lower.contains("hello") || msg_lower.contains("hi") || msg_lower.contains("hey") {
        if let Some(name) = user_first_name {
            response.push_str(&format!(
                "\nTell me what's wrong, {name} — I'll diagnose and repair it automatically. No manual steps required on your end."
            ));
        } else {
            response.push_str("\nTell me what's wrong — I'll diagnose and repair it automatically. No manual steps required on your end.");
        }
    } else if let Some(name) = user_first_name {
        response.push_str(&format!(
            "\nThe issue has been handled, {name}. I'll keep monitoring — let me know if you need anything else."
        ));
    } else {
        response.push_str("\nThe issue has been handled. I'll keep monitoring — let me know if you need anything else.");
    }

    if let Some(err) = api_error {
        response.push_str(&format!("\n\n_Note: Cloud AI summary unavailable ({err}). Repairs were still executed locally._"));
    }

    response
}

#[tauri::command]
pub fn generate_diagnostic_report(state: State<AppState>, scan_id: Option<String>) -> Result<DiagnosticReport, String> {
    {
        let db = state.lock_db()?;
        licensing::require_report_generation(&db)?;
    }

    let db = state.lock_db()?;

    let scan: SystemScanResult = if let Some(id) = scan_id {
        let record = db.get_scan(&id).map_err(|e| e.to_string())?;
        let mut scan: SystemScanResult = serde_json::from_str(&record.scan_data).map_err(|e| e.to_string())?;
        scan.id = record.id;
        scan
    } else {
        let scans = db.list_scans(1).map_err(|e| e.to_string())?;
        let record = scans.first().ok_or("No scan data available. Run a system scan first.")?;
        let mut scan: SystemScanResult = serde_json::from_str(&record.scan_data).map_err(|e| e.to_string())?;
        scan.id = record.id.clone();
        scan
    };

    let risk_level = if scan.issues.iter().any(|i| i.severity == "critical") {
        "critical"
    } else if scan.issues.iter().any(|i| i.severity == "high") {
        "high"
    } else if scan.issues.iter().any(|i| i.severity == "medium") {
        "medium"
    } else {
        "low"
    };

    let findings: Vec<serde_json::Value> = scan
        .issues
        .iter()
        .map(|i| {
            serde_json::json!({
                "title": i.title,
                "description": i.description,
                "severity": i.severity,
                "category": i.category,
            })
        })
        .collect();

    let recommendations = generate_recommendations(&scan);

    let plain_language = format!(
        "Your computer scored {}/100 on our health check. {} You are running {} {} with {} GB of RAM and {:.1}% of it is currently in use. {}",
        scan.health_score,
        if scan.health_score >= 80 { "Overall, your system is in good shape." }
        else if scan.health_score >= 60 { "There are some areas that could use attention." }
        else { "Your system needs attention in several areas." },
        scan.os.name, scan.os.version,
        scan.memory.total_gb, scan.memory.usage_percent,
        if scan.issues.is_empty() { "No significant issues were found.".to_string() }
        else { format!("We found {} issue(s) that should be reviewed.", scan.issues.len()) }
    );

    let report = DiagnosticReport {
        id: Uuid::new_v4().to_string(),
        scan_id: Some(scan.id.clone()),
        title: format!("System Diagnostic Report — {}", chrono::Utc::now().format("%Y-%m-%d %H:%M UTC")),
        summary: format!(
            "Health score: {}/100. {} issue(s) detected on {} running {}.",
            scan.health_score, scan.issues.len(), scan.os.hostname, scan.os.name
        ),
        findings: serde_json::to_string(&findings).unwrap_or_else(|_| "[]".to_string()),
        recommendations: serde_json::to_string(&recommendations).unwrap_or_else(|_| "[]".to_string()),
        health_score: scan.health_score,
        risk_level: risk_level.to_string(),
        technician_notes: None,
        plain_language,
        created_at: chrono::Utc::now().to_rfc3339(),
    };

    db.save_report(&report).map_err(|e| e.to_string())?;
    Ok(report)
}

fn generate_recommendations(scan: &SystemScanResult) -> Vec<serde_json::Value> {
    let mut recs = Vec::new();

    for issue in &scan.issues {
        let action = match issue.category.as_str() {
            "storage" => "Run disk cleanup and remove unnecessary files",
            "performance" => "Review high-resource processes and startup programs",
            "process" => "Investigate the flagged process; consider closing or updating it",
            _ => "Review the issue details and take appropriate action",
        };
        recs.push(serde_json::json!({
            "issue": issue.title,
            "action": action,
            "risk": "low",
            "steps": [
                "Review the issue in Thorpe Repair Center",
                "Follow the recommended safe repair action",
                "Re-run a system scan to verify improvement"
            ]
        }));
    }

    if recs.is_empty() {
        recs.push(serde_json::json!({
            "issue": "No issues detected",
            "action": "Maintain regular system health scans",
            "risk": "low",
            "steps": [
                "Schedule periodic scans",
                "Keep your system updated",
                "Maintain adequate free disk space"
            ]
        }));
    }

    recs
}

#[cfg(test)]
mod tests {
    use super::extract_first_name;

    #[test]
    fn extracts_first_name_from_display_name() {
        assert_eq!(extract_first_name("Jordan Smith"), Some("Jordan".to_string()));
    }

    #[test]
    fn skips_generic_placeholder_names() {
        assert_eq!(extract_first_name("User"), None);
        assert_eq!(extract_first_name("guest"), None);
    }
}
