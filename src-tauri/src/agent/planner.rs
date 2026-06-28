use crate::repairs::{action_kind, plan_repairs};
use crate::scanner::SystemScanResult;
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentPlan {
    pub hypotheses: Vec<String>,
    pub confidence: f64,
    pub steps: Vec<AgentPlanStep>,
    pub citations: Vec<String>,
    pub escalate_if: Vec<String>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct AgentPlanStep {
    pub tool_id: String,
    pub reason: String,
    pub risk: String,
    pub requires_approval: bool,
}

#[derive(Debug, Clone)]
pub struct PlannerContext {
    pub message: String,
    pub scan_json: Option<String>,
    pub evidence_json: Option<String>,
    pub kb_excerpts: Vec<String>,
    pub intel_excerpts: Vec<String>,
    pub available_tools: Vec<String>,
}

#[derive(Debug, Deserialize)]
struct LlmPlanResponse {
    hypotheses: Vec<String>,
    confidence: f64,
    steps: Vec<AgentPlanStep>,
    citations: Vec<String>,
    escalate_if: Vec<String>,
}

pub fn plan_with_rules(message: &str, scan: Option<&SystemScanResult>) -> AgentPlan {
    let tool_ids = plan_repairs(message, scan);
    AgentPlan {
        hypotheses: vec![format!("User reported: {}", message.chars().take(120).collect::<String>())],
        confidence: if scan.is_some() { 0.65 } else { 0.5 },
        steps: tool_ids
            .into_iter()
            .map(|tool_id| AgentPlanStep {
                requires_approval: action_kind(&tool_id) == "mutating",
                risk: if action_kind(&tool_id) == "mutating" {
                    "medium".into()
                } else {
                    "low".into()
                },
                reason: format!("Rule-based planner selected {tool_id}"),
                tool_id,
            })
            .collect(),
        citations: vec![],
        escalate_if: vec![],
    }
}

pub async fn plan_with_llm(
    ctx: &PlannerContext,
    enterprise: Option<&crate::enterprise_ai::ResolvedAiRuntime>,
) -> Result<AgentPlan, String> {
    let user_api = enterprise.is_none().then(|| load_user_api_config()).flatten();

    let (base_url, model, api_key) = if let Some(rt) = enterprise {
        (rt.base_url.clone(), rt.model.clone(), rt.api_key.clone())
    } else if let Some((url, model, key)) = user_api {
        (url, model, key)
    } else {
        return Err("No LLM configured".into());
    };

    let system = r#"You are Jonathan, a senior IT systems engineer planning incident response.
Output ONLY valid JSON matching this schema:
{
  "hypotheses": ["string"],
  "confidence": 0.0-1.0,
  "steps": [{"tool_id": "string", "reason": "string", "risk": "low|medium|high", "requires_approval": bool}],
  "citations": ["string"],
  "escalate_if": ["string"]
}
Rules:
- Only use tool_id values from the provided available_tools list
- Prefer diagnostics before mutating repairs
- Set requires_approval true for mutating tools
- confidence below 0.55 means uncertain — add escalate_if conditions
- Cite KB/intel excerpts when used"#;

    let user_content = serde_json::json!({
        "message": ctx.message,
        "scan": ctx.scan_json,
        "evidence": ctx.evidence_json,
        "knowledge": ctx.kb_excerpts,
        "intel": ctx.intel_excerpts,
        "available_tools": ctx.available_tools,
    });

    let client = reqwest::Client::new();
    let response = client
        .post(format!("{}/chat/completions", base_url.trim_end_matches('/')))
        .header("Authorization", format!("Bearer {api_key}"))
        .header("Content-Type", "application/json")
        .json(&serde_json::json!({
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user_content.to_string()}
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
            "max_tokens": 1500,
        }))
        .send()
        .await
        .map_err(|e| e.to_string())?;

    if !response.status().is_success() {
        return Err(format!("Planner LLM error: {}", response.status()));
    }

    #[derive(Deserialize)]
    struct Wrapper {
        choices: Vec<Choice>,
    }
    #[derive(Deserialize)]
    struct Choice {
        message: Msg,
    }
    #[derive(Deserialize)]
    struct Msg {
        content: String,
    }

    let wrapper: Wrapper = response.json().await.map_err(|e| e.to_string())?;
    let content = wrapper
        .choices
        .first()
        .map(|c| c.message.content.clone())
        .ok_or_else(|| "Empty planner response".to_string())?;

    let parsed: LlmPlanResponse = serde_json::from_str(&content).map_err(|e| format!("Invalid plan JSON: {e}"))?;
    Ok(AgentPlan {
        hypotheses: parsed.hypotheses,
        confidence: parsed.confidence.clamp(0.0, 1.0),
        steps: parsed
            .steps
            .into_iter()
            .filter(|s| ctx.available_tools.contains(&s.tool_id))
            .collect(),
        citations: parsed.citations,
        escalate_if: parsed.escalate_if,
    })
}

fn load_user_api_config() -> Option<(String, String, String)> {
    None
}

pub async fn plan_with_llm_user(
    ctx: &PlannerContext,
    base_url: &str,
    model: &str,
    api_key: &str,
) -> Result<AgentPlan, String> {
    let rt = crate::enterprise_ai::ResolvedAiRuntime {
        provider_id: "user".into(),
        provider_type: "openai".into(),
        base_url: base_url.to_string(),
        model: model.to_string(),
        api_key: api_key.to_string(),
    };
    plan_with_llm(ctx, Some(&rt)).await
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn rule_planner_produces_steps() {
        let plan = plan_with_rules("wifi not working", None);
        assert!(!plan.steps.is_empty());
        assert!(plan.steps.iter().any(|s| s.tool_id == "dns-flush"));
    }
}
