use crate::db::DiagnosticReport;
use crate::licensing;
use crate::scanner::SystemScanResult;
use crate::AppState;
use serde::{Deserialize, Serialize};
use tauri::State;
use uuid::Uuid;

const JONATHAN_SYSTEM_PROMPT: &str = r#"You are Jonathan, a senior IT support technician built into Thorpe, an enterprise IT support platform.

Personality and communication:
- Knowledgeable, patient, and professional
- Explain technical concepts clearly and safely
- Adapt explanations to the user's skill level (beginner or advanced)
- Never invent system information — only reference data explicitly provided
- Clearly distinguish facts from suggestions
- Warn before any potentially risky operation
- Escalate to a human technician when appropriate

Security rules (NEVER violate):
- Never request passwords, security answers, recovery codes, or credentials
- Never suggest disabling security software without clear justification
- Never recommend downloading from untrusted sources
- Never perform actions without user consent

Capabilities:
- Windows, macOS, and Linux troubleshooting
- Wi-Fi, networking, printers, VPNs, email configuration
- Performance, startup, driver, storage, security, and update guidance
- Basic command-line assistance with clear explanations

When system scan data is provided, base your analysis ONLY on that data.
Format responses with clear sections when providing diagnostic information."#;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AiConfig {
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
    let db = state.db.lock().unwrap();
    Ok(AiConfig {
        provider: db.get_setting("ai_provider").ok().flatten().unwrap_or_else(|| "openai".to_string()),
        api_key: db.get_setting("ai_api_key").ok().flatten(),
        model: db.get_setting("ai_model").ok().flatten().unwrap_or_else(|| "gpt-4o-mini".to_string()),
        base_url: db.get_setting("ai_base_url").ok().flatten().unwrap_or_else(|| "https://api.openai.com/v1".to_string()),
        enabled: db.get_setting("ai_enabled").ok().flatten().map(|v| v == "true").unwrap_or(false),
    })
}

#[tauri::command]
pub fn set_ai_config(state: State<AppState>, config: AiConfig) -> Result<(), String> {
    let db = state.db.lock().unwrap();
    db.set_setting("ai_provider", &config.provider).map_err(|e| e.to_string())?;
    if let Some(key) = &config.api_key {
        db.set_setting("ai_api_key", key).map_err(|e| e.to_string())?;
    }
    db.set_setting("ai_model", &config.model).map_err(|e| e.to_string())?;
    db.set_setting("ai_base_url", &config.base_url).map_err(|e| e.to_string())?;
    db.set_setting("ai_enabled", if config.enabled { "true" } else { "false" }).map_err(|e| e.to_string())?;
    Ok(())
}

#[tauri::command]
pub async fn chat_with_jonathan(state: State<'_, AppState>, request: ChatRequest) -> Result<ChatResponse, String> {
    let config = get_ai_config(state.clone())?;

    state.db.lock().unwrap().save_chat("user", &request.message).ok();

    let response = if config.enabled && config.api_key.is_some() {
        match call_openai(&config, &request).await {
            Ok(msg) => ChatResponse { message: msg, source: "openai".to_string() },
            Err(e) => {
                let fallback = generate_local_response(&request, &e);
                ChatResponse { message: fallback, source: "local".to_string() }
            }
        }
    } else {
        let fallback = generate_local_response(&request, "");
        ChatResponse { message: fallback, source: "local".to_string() }
    };

    state.db.lock().unwrap().save_chat("assistant", &response.message).ok();
    Ok(response)
}

async fn call_openai(config: &AiConfig, request: &ChatRequest) -> Result<String, String> {
    let api_key = config.api_key.as_ref().ok_or("No API key configured")?;

    let skill_context = match request.skill_level.as_str() {
        "advanced" => "The user is technically advanced. You may use technical terminology.",
        _ => "The user is a beginner. Use plain language and avoid jargon.",
    };

    let mut system_prompt = format!("{}\n\n{}", JONATHAN_SYSTEM_PROMPT, skill_context);
    if let Some(ctx) = &request.scan_context {
        system_prompt.push_str(&format!("\n\nCurrent system scan data:\n{}", ctx));
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

fn generate_local_response(request: &ChatRequest, api_error: &str) -> String {
    let msg_lower = request.message.to_lowercase();

    if msg_lower.contains("password") || msg_lower.contains("credential") {
        return "I can't help with passwords or credentials — that's a security boundary I never cross. If you've forgotten a password, use your system's official recovery options or contact your IT administrator.".to_string();
    }

    if msg_lower.contains("hello") || msg_lower.contains("hi") || msg_lower.contains("hey") {
        return "Hello! I'm Jonathan, your AI IT technician. I'm here to help you diagnose and resolve computer issues safely.\n\nYou can:\n- Run a **System Health Scan** to check your computer\n- Ask me about specific problems (Wi-Fi, printers, performance, etc.)\n- Browse the **Knowledge Base** for step-by-step guides\n\nWhat can I help you with today?".to_string();
    }

    if msg_lower.contains("wifi") || msg_lower.contains("wi-fi") || msg_lower.contains("internet") || msg_lower.contains("network") {
        return "Let me help with your network issue.\n\n**Quick steps to try:**\n1. Toggle Wi-Fi off and back on\n2. Restart your router/modem (unplug for 30 seconds)\n3. Try flushing the DNS cache (available in Repair Center)\n4. Check if other devices can connect\n\n**Facts vs. suggestions:**\n- *Fact:* If other devices work, the issue is likely on this computer\n- *Suggestion:* Switching to a wired connection can help isolate Wi-Fi-specific problems\n\nWould you like me to run a system scan to check your network configuration?".to_string();
    }

    if msg_lower.contains("slow") || msg_lower.contains("performance") {
        return "Performance issues can have several causes. Here's a systematic approach:\n\n**Check these areas:**\n1. **Disk space** — Less than 10% free can slow everything down\n2. **Memory usage** — Too many open apps consume RAM\n3. **Startup programs** — Unnecessary startup items slow boot time\n4. **Updates** — Pending updates can cause temporary slowdowns\n\n**Recommended actions:**\n- Run a System Health Scan for specific findings\n- Use Repair Center > \"Identify High Resource Usage\"\n- Review startup programs\n\n⚠️ I won't make changes without your explicit approval.".to_string();
    }

    if msg_lower.contains("printer") || msg_lower.contains("print") {
        return "Let's troubleshoot your printing issue.\n\n**Safe steps to try:**\n1. Check that the printer is powered on and connected\n2. Cancel stuck jobs in the print queue\n3. Power cycle the printer (off for 30 seconds)\n4. Update or reinstall printer drivers\n\n**On Windows:** Repair Center can restart the Print Spooler service (requires your confirmation).\n\n**When to escalate:** If the printer shows hardware error codes or physical damage.".to_string();
    }

    if msg_lower.contains("virus") || msg_lower.contains("malware") || msg_lower.contains("ransomware") {
        return "⚠️ **Security concern detected in your message.**\n\n**If you suspect malware:**\n1. Disconnect from the network immediately (especially for ransomware)\n2. Run a full antivirus scan\n3. Do NOT pay ransom demands\n4. Change passwords from a clean device\n\n**If ransomware is involved:** Stop using this computer and contact a cybersecurity professional immediately.\n\nI can help guide you through safe diagnostic steps, but I will never ask for passwords or suggest disabling your security software.".to_string();
    }

    if let Some(ctx) = &request.scan_context {
        return format!(
            "Based on your system scan data, here's my analysis:\n\n{}\n\n**Note:** I'm operating in local mode (cloud AI is not configured). For more detailed analysis, enable cloud AI in Settings with your OpenAI API key.\n\nWould you like specific recommendations for any of the detected issues?",
            summarize_scan_context(ctx)
        );
    }

    let api_note = if !api_error.is_empty() {
        format!("\n\n_Note: Cloud AI is temporarily unavailable ({}). I'm providing guidance from my built-in knowledge._", api_error)
    } else {
        "\n\n_Tip: Enable cloud AI in Settings for more personalized responses._".to_string()
    };

    format!(
        "I understand you're asking about: \"{}\"\n\nHere's my guidance:\n\n1. **Gather information** — Run a System Health Scan so I can analyze your actual system state\n2. **Check the Knowledge Base** — Search for articles related to your issue\n3. **Try safe repairs** — Repair Center offers low-risk maintenance tools\n\nCould you provide more details about the specific symptoms you're experiencing? For example:\n- When did the problem start?\n- Does it happen consistently or intermittently?\n- Any error messages?{}",
        request.message, api_note
    )
}

fn summarize_scan_context(ctx: &str) -> String {
    if let Ok(scan) = serde_json::from_str::<SystemScanResult>(ctx) {
        let mut summary = format!(
            "**System Health Score: {}/100**\n\n**OS:** {} {}\n**CPU:** {} ({:.1}% usage)\n**Memory:** {:.1} GB / {:.1} GB ({:.1}%)\n",
            scan.health_score, scan.os.name, scan.os.version, scan.cpu.brand, scan.cpu.usage_percent,
            scan.memory.used_gb, scan.memory.total_gb, scan.memory.usage_percent
        );
        if !scan.issues.is_empty() {
            summary.push_str("\n**Detected Issues:**\n");
            for issue in &scan.issues {
                summary.push_str(&format!("- [{}] {}: {}\n", issue.severity.to_uppercase(), issue.title, issue.description));
            }
        } else {
            summary.push_str("\nNo significant issues detected.\n");
        }
        summary
    } else {
        "Scan data available but could not be parsed for summary.".to_string()
    }
}

#[tauri::command]
pub fn generate_diagnostic_report(state: State<AppState>, scan_id: Option<String>) -> Result<DiagnosticReport, String> {
    {
        let db = state.db.lock().unwrap();
        licensing::require_report_generation(&db)?;
    }

    let db = state.db.lock().unwrap();

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
