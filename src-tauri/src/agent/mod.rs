mod planner;

pub use planner::{plan_with_llm, plan_with_rules, AgentPlan, AgentPlanStep, PlannerContext};

use crate::db::{AgentSessionRecord, CreateCase};
use crate::evidence::{self, SystemEvidence};
use crate::integrations::psa;
use crate::licensing;
use crate::repairs::{self, RepairAction, RepairResult};
use crate::scanner::{self, SystemScanResult};
use crate::AppState;
use chrono::Utc;
use serde::{Deserialize, Serialize};
use tauri::State;
use uuid::Uuid;

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct RepairVerification {
    pub health_before: i32,
    pub health_after: i32,
    pub issues_before: usize,
    pub issues_after: usize,
    pub improved: bool,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct KbSuggestion {
    pub id: String,
    pub title: String,
    pub summary: String,
    pub source: String,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentSessionSummary {
    pub session_id: String,
    pub plan: AgentPlan,
    pub evidence: SystemEvidence,
    pub citations: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct IncidentResult {
    pub repairs_executed: Vec<RepairResult>,
    pub pending_repairs: Vec<RepairAction>,
    pub verification: Option<RepairVerification>,
    pub escalation_case_id: Option<String>,
    pub kb_suggestions: Vec<KbSuggestion>,
    pub agent_session: Option<AgentSessionSummary>,
    pub connectivity_report: Option<crate::connectivity::ConnectivityReport>,
}

pub async fn orchestrate_incident(
    state: &State<'_, AppState>,
    message: &str,
    scan: &Option<SystemScanResult>,
    confirmed_repairs: &[String],
) -> IncidentResult {
    let session_id = Uuid::new_v4().to_string();
    let evidence = evidence::collect_system_evidence(scan.as_ref());

    if let Ok(db) = state.lock_db() {
        let _ = db.save_evidence(
            &session_id,
            "collector",
            "system_evidence",
            &serde_json::to_string(&evidence).unwrap_or_default(),
        );
        if let Some(s) = scan {
            let _ = db.save_evidence(
                &session_id,
                "scanner",
                "scan_snapshot",
                &serde_json::to_string(s).unwrap_or_default(),
            );
        }
        let _ = crate::intel::ensure_intel_seeded(&db);
        let _ = crate::repairs::ensure_packs_installed(&db);
    }

    if let Some(reason) = security_escalation(message) {
        let escalation_case_id = state.lock_db().ok().and_then(|db| {
            let case = CreateCase {
                client_id: None,
                device_id: None,
                title: "Jonathan security escalation".into(),
                status: "open".into(),
                priority: "high".into(),
                description: Some(format!("{reason}\n\nUser message: {message}")),
                report_id: None,
            };
            let created = db.create_case(&case).ok()?;
            psa::spawn_case_event(state, "case.escalated", created.clone());
            Some(created.id)
        });
        return IncidentResult {
            repairs_executed: vec![],
            pending_repairs: vec![],
            verification: None,
            escalation_case_id,
            kb_suggestions: vec![],
            agent_session: None,
            connectivity_report: None,
        };
    }

    let connectivity_report = if crate::connectivity::is_connectivity_issue(message) {
        let report = crate::connectivity::run_connectivity_suite();
        if let Ok(db) = state.lock_db() {
            let record = crate::db::ConnectivityDiagnosticRecord {
                id: Uuid::new_v4().to_string(),
                session_id: Some(session_id.clone()),
                user_message: Some(message.chars().take(500).collect()),
                overall_status: report.overall_status.clone(),
                playbook_summary: report.playbook_summary.clone(),
                results_json: serde_json::to_string(&report.checks).unwrap_or_else(|_| "[]".into()),
                recommended_actions_json: serde_json::to_string(&report.recommended_actions)
                    .unwrap_or_else(|_| "[]".into()),
                created_at: Utc::now().to_rfc3339(),
            };
            let _ = db.save_connectivity_diagnostic(&record);
            let _ = db.save_evidence(
                &session_id,
                "connectivity",
                "offline_connectivity_suite",
                &serde_json::to_string(&report).unwrap_or_default(),
            );
        }
        Some(report)
    } else {
        None
    };

    let plan = build_plan(state, message, scan, &evidence).await;
    let tool_ids: Vec<String> = plan
        .steps
        .iter()
        .map(|s| s.tool_id.clone())
        .collect();

    let mut filtered = filter_allowed_tools(state, &tool_ids);
    if connectivity_report.is_some() {
        filtered.retain(|id| id != "connectivity-suite");
    }
    let repair_plan = repairs::plan_chat_repairs(&filtered, confirmed_repairs);

    let health_before = scan.as_ref().map(|s| s.health_score).unwrap_or(0);
    let issues_before = scan.as_ref().map(|s| s.issues.len()).unwrap_or(0);

    let repairs_executed = state
        .lock_db()
        .ok()
        .map(|db| repairs::perform_repairs_with_failures(&db, &repair_plan.to_run))
        .unwrap_or_default();

    let verification = if repairs::any_mutating_success(&repairs_executed) {
        let after = scanner::quick_system_scan();
        Some(RepairVerification {
            health_before,
            health_after: after.health_score,
            issues_before,
            issues_after: after.issues.len(),
            improved: after.health_score > health_before || after.issues.len() < issues_before,
        })
    } else {
        None
    };

    let kb_suggestions = gather_kb(state, message);
    let agent_session = persist_session(state, &session_id, message, &plan, &evidence, "completed");

    if plan.confidence < 0.55 {
        let _ = escalation_on_low_confidence(state, message, &plan);
    }

    IncidentResult {
        repairs_executed,
        pending_repairs: repair_plan.pending_confirmation,
        verification,
        escalation_case_id: None,
        kb_suggestions,
        agent_session,
        connectivity_report,
    }
}

async fn build_plan(
    state: &State<'_, AppState>,
    message: &str,
    scan: &Option<SystemScanResult>,
    evidence: &SystemEvidence,
) -> AgentPlan {
    let ctx = build_planner_context(state, message, scan, evidence);
    if let Ok(runtime) = try_enterprise_runtime(state) {
        if let Ok(plan) = plan_with_llm(&ctx, Some(&runtime)).await {
            if !plan.steps.is_empty() {
                return plan;
            }
        }
    }
    if let Some(runtime) = try_user_runtime(state) {
        if let Ok(plan) = plan_with_llm(&ctx, Some(&runtime)).await {
            if !plan.steps.is_empty() {
                return plan;
            }
        }
    }
    planner::plan_with_rules(message, scan.as_ref())
}

fn try_user_runtime(state: &State<AppState>) -> Option<crate::enterprise_ai::ResolvedAiRuntime> {
    let api_key = crate::secrets::get_api_key(&state.data_dir).ok()??;
    if api_key.is_empty() {
        return None;
    }
    let db = state.lock_db().ok()?;
    let enabled = db
        .get_setting("ai_enabled")
        .ok()
        .flatten()
        .map(|v| v == "true")
        .unwrap_or(false);
    if !enabled {
        return None;
    }
    Some(crate::enterprise_ai::ResolvedAiRuntime {
        provider_id: "user-settings".into(),
        provider_type: "openai".into(),
        base_url: db
            .get_setting("ai_base_url")
            .ok()
            .flatten()
            .unwrap_or_else(|| "https://api.openai.com/v1".to_string()),
        model: db
            .get_setting("ai_model")
            .ok()
            .flatten()
            .unwrap_or_else(|| "gpt-4o-mini".to_string()),
        api_key,
    })
}

fn try_enterprise_runtime(
    state: &State<'_, AppState>,
) -> Result<crate::enterprise_ai::ResolvedAiRuntime, String> {
    let db = state.lock_db()?;
    crate::enterprise_ai::resolve_runtime(&db, &state.data_dir, "jonathan")
        .and_then(|r| r.ok_or_else(|| "No enterprise runtime".to_string()))
}

fn build_planner_context(
    state: &State<'_, AppState>,
    message: &str,
    scan: &Option<SystemScanResult>,
    evidence: &SystemEvidence,
) -> PlannerContext {
    let (kb, intel) = state.lock_db().map(|db| {
        (
            db.search_knowledge_for_message(message, 3).unwrap_or_default(),
            db.search_intel_for_message(message, 3).unwrap_or_default(),
        )
    }).unwrap_or_default();

    let available_tools: Vec<String> = state
        .lock_db()
        .ok()
        .and_then(|db| crate::repairs::allowed_tool_ids(&db).ok())
        .unwrap_or_else(|| repairs::plan_repairs(message, scan.as_ref()));

    PlannerContext {
        message: message.to_string(),
        scan_json: scan
            .as_ref()
            .and_then(|s| serde_json::to_string(s).ok()),
        evidence_json: serde_json::to_string(evidence).ok(),
        kb_excerpts: kb
            .iter()
            .map(|a| format!("{}: {}", a.title, a.symptoms.chars().take(200).collect::<String>()))
            .collect(),
        intel_excerpts: intel
            .iter()
            .map(|i| format!("[{}] {}: {}", i.severity, i.title, i.summary))
            .collect(),
        available_tools,
    }
}

fn filter_allowed_tools(state: &State<AppState>, tool_ids: &[String]) -> Vec<String> {
    let allowed = state
        .lock_db()
        .ok()
        .and_then(|db| crate::repairs::allowed_tool_ids(&db).ok())
        .unwrap_or_default();
    tool_ids
        .iter()
        .filter(|t| allowed.contains(t))
        .cloned()
        .collect()
}

fn gather_kb(state: &State<AppState>, message: &str) -> Vec<KbSuggestion> {
    let Ok(db) = state.lock_db() else {
        return vec![];
    };
    let mut out = Vec::new();
    for article in db.search_knowledge_for_message(message, 2).unwrap_or_default() {
        out.push(KbSuggestion {
            id: article.id.clone(),
            title: article.title.clone(),
            summary: article.symptoms.chars().take(160).collect(),
            source: "knowledge_base".into(),
        });
    }
    for item in db.search_intel_for_message(message, 2).unwrap_or_default() {
        out.push(KbSuggestion {
            id: item.id.clone(),
            title: item.title.clone(),
            summary: item.summary.chars().take(160).collect(),
            source: format!("intel:{}", item.source),
        });
    }
    out
}

fn persist_session(
    state: &State<'_, AppState>,
    session_id: &str,
    message: &str,
    plan: &AgentPlan,
    evidence: &SystemEvidence,
    status: &str,
) -> Option<AgentSessionSummary> {
    let Ok(db) = state.lock_db() else {
        return None;
    };
    let record = AgentSessionRecord {
        id: session_id.to_string(),
        case_id: None,
        message: message.to_string(),
        plan_json: serde_json::to_string(plan).ok()?,
        evidence_json: serde_json::to_string(evidence).ok(),
        status: status.to_string(),
        confidence: plan.confidence,
        created_at: Utc::now().to_rfc3339(),
    };
    db.save_agent_session(&record).ok()?;
    psa::spawn_agent_session(state, record.clone());
    Some(AgentSessionSummary {
        session_id: session_id.to_string(),
        plan: plan.clone(),
        evidence: evidence.clone(),
        citations: plan.citations.clone(),
    })
}

fn security_escalation(message: &str) -> Option<&'static str> {
    let m = message.to_lowercase();
    if m.contains("virus") || m.contains("malware") || m.contains("ransomware") {
        return Some("Potential malware reported");
    }
    if m.contains("password") || m.contains("credential") {
        return Some("Credential boundary");
    }
    None
}
fn escalation_on_low_confidence(
    state: &State<'_, AppState>,
    message: &str,
    plan: &AgentPlan,
) -> Option<String> {
    if plan.confidence >= 0.55 {
        return None;
    }
    let db = state.lock_db().ok()?;
    let case = CreateCase {
        client_id: None,
        device_id: None,
        title: "Jonathan low-confidence escalation".into(),
        status: "open".into(),
        priority: "medium".into(),
        description: Some(format!(
            "Confidence {:.0}%. Message: {}\nHypotheses: {}",
            plan.confidence * 100.0,
            message,
            plan.hypotheses.join("; ")
        )),
        report_id: None,
    };
    db.create_case(&case).ok().map(|created| {
        psa::spawn_case_event(state, "case.escalated", created.clone());
        created.id
    })
}

#[tauri::command]
pub fn list_agent_sessions(state: State<AppState>, limit: Option<i64>) -> Result<Vec<AgentSessionRecord>, String> {
    let db = state.lock_db()?;
    licensing::require_feature(&db, "intelligence_console")?;
    db.list_agent_sessions(limit.unwrap_or(50))
        .map_err(|e| e.to_string())
}

#[tauri::command]
pub async fn sync_intel_feed(state: State<'_, AppState>) -> Result<i64, String> {
    let url = {
        let db = state.lock_db()?;
        licensing::require_feature(&db, "intelligence_console")?;
        db.get_setting("intel_feed_url").ok().flatten()
    };
    tokio::task::block_in_place(|| {
        tauri::async_runtime::block_on(async {
            let db = state.lock_db()?;
            crate::intel::sync_intel_feed(&db, url.as_deref()).await
        })
    })
}

#[tauri::command]
pub fn list_intel_items(state: State<AppState>, limit: Option<i64>) -> Result<Vec<crate::db::IntelItem>, String> {
    let db = state.lock_db()?;
    licensing::require_feature(&db, "intelligence_console")?;
    crate::intel::ensure_intel_seeded(&db)?;
    db.list_intel_items(limit.unwrap_or(50)).map_err(|e| e.to_string())
}

#[tauri::command]
pub fn list_repair_packs(state: State<AppState>) -> Result<Vec<crate::db::RepairPackRecord>, String> {
    let db = state.lock_db()?;
    licensing::require_feature(&db, "intelligence_console")?;
    crate::repairs::ensure_packs_installed(&db)?;
    db.list_repair_packs().map_err(|e| e.to_string())
}

#[tauri::command]
pub fn install_repair_pack(state: State<AppState>, manifest_json: String) -> Result<crate::db::RepairPackRecord, String> {
    let db = state.lock_db()?;
    licensing::require_feature(&db, "intelligence_console")?;
    crate::repairs::install_pack_from_json(&db, &manifest_json)
}

#[tauri::command]
pub fn upsert_org_playbook(
    state: State<AppState>,
    title: String,
    category: String,
    content: String,
    tags: Vec<String>,
) -> Result<crate::db::OrgPlaybook, String> {
    let db = state.lock_db()?;
    licensing::require_feature(&db, "intelligence_console")?;
    crate::intel::create_playbook(&db, &title, &category, &content, &tags)
}

#[tauri::command]
pub fn list_org_playbooks(state: State<AppState>) -> Result<Vec<crate::db::OrgPlaybook>, String> {
    let db = state.lock_db()?;
    licensing::require_feature(&db, "intelligence_console")?;
    db.list_org_playbooks().map_err(|e| e.to_string())
}
