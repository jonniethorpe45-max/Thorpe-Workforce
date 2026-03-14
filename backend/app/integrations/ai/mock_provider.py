import json
from typing import Any

from app.integrations.ai.base import AIProvider, CompanyResearchResult, OutreachEmailResult, ReplyClassificationResult, WorkerModelResponse
from app.services.ai_utils import (
    clamp_score,
    enforce_single_cta,
    enforce_word_limit,
    normalize_whitespace,
    parse_json_object,
    sanitize_list,
)


class MockAIProvider(AIProvider):
    def generate_company_research(self, company_name: str, website: str | None, industry: str | None) -> CompanyResearchResult:
        raw_response = json.dumps(
            {
                "summary": (
                    f"{company_name} appears to be scaling GTM execution and likely needs more consistent outbound throughput."
                ),
                "pain_points": [
                    "Pipeline inconsistency across reps",
                    "Slow follow-up cadence causing lead decay",
                    "Limited personalization at scale",
                ],
                "relevance_score": 0.82,
                "personalization_hook": (
                    f"Noticed {company_name}'s momentum in {industry or 'their market'} and thought this could support outbound scale."
                ),
            }
        )
        parsed = parse_json_object(
            raw_response,
            fallback={
                "summary": f"{company_name} is a potential fit for AI-assisted outbound support.",
                "pain_points": ["Pipeline inconsistency", "Manual personalization bottlenecks"],
                "relevance_score": 0.7,
                "personalization_hook": f"Thought a predictable outbound rhythm could help {company_name}.",
            },
        )
        return CompanyResearchResult(
            summary=normalize_whitespace(parsed.get("summary", "")) or f"{company_name} is a potential fit.",
            pain_points=sanitize_list(parsed.get("pain_points"), max_items=4) or ["Outbound consistency", "Lead follow-up"],
            relevance_score=clamp_score(parsed.get("relevance_score"), default=0.7),
            personalization_hook=normalize_whitespace(parsed.get("personalization_hook", ""))
            or f"Thought a simple outbound operating cadence could help {company_name}.",
            model="mock-ai-v1",
        )

    def generate_outreach_email(self, lead_name: str, company_name: str, title: str | None, cta: str) -> OutreachEmailResult:
        raw_response = json.dumps(
            {
                "subject": f"Idea for {company_name}'s outbound pipeline",
                "body": (
                    f"Hi {lead_name},\n\n"
                    f"We help teams like {company_name} run high-quality outbound without increasing headcount. "
                    f"I noticed your focus on {title or 'revenue outcomes'} and thought this could be useful.\n\n"
                    "Best,\nThorpe Workforce"
                ),
                "personalization": {"type": "role_context", "title": title or "unknown"},
            }
        )
        parsed = parse_json_object(
            raw_response,
            fallback={
                "subject": f"Quick idea for {company_name}",
                "body": f"Hi {lead_name}, we help teams improve outbound consistency.",
                "personalization": {"type": "fallback"},
            },
        )
        body = enforce_single_cta(enforce_word_limit(parsed.get("body", ""), max_words=120), cta)
        return OutreachEmailResult(
            subject=normalize_whitespace(parsed.get("subject", "")) or f"Quick idea for {company_name}",
            body=body,
            personalization=parsed.get("personalization", {}) if isinstance(parsed.get("personalization"), dict) else {},
        )

    def generate_followup_email(self, lead_name: str, company_name: str, step: int, cta: str) -> OutreachEmailResult:
        raw_response = json.dumps(
            {
                "subject": f"Quick follow-up on outbound at {company_name}",
                "body": (
                    f"Hi {lead_name},\n\n"
                    "Following up in case timing is better now. We help teams automate research, drafting, and follow-up "
                    "while keeping messaging personal.\n\nRegards,\nThorpe Workforce"
                ),
                "personalization": {"step": step},
            }
        )
        parsed = parse_json_object(
            raw_response,
            fallback={
                "subject": f"Following up from Thorpe Workforce",
                "body": f"Hi {lead_name}, circling back in case this is relevant.",
                "personalization": {"step": step},
            },
        )
        body = enforce_single_cta(enforce_word_limit(parsed.get("body", ""), max_words=120), cta)
        personalization = parsed.get("personalization", {})
        if not isinstance(personalization, dict):
            personalization = {"step": step}
        return OutreachEmailResult(
            subject=normalize_whitespace(parsed.get("subject", "")) or f"Following up with {company_name}",
            body=body,
            personalization=personalization,
        )

    def classify_reply(self, reply_text: str) -> ReplyClassificationResult:
        text = reply_text.lower()
        classification = {"intent": "unknown", "confidence": 0.55, "requires_human_review": True, "sentiment": "neutral"}
        if "unsubscribe" in text:
            classification = {"intent": "unsubscribe", "confidence": 0.99, "requires_human_review": False, "sentiment": "neutral"}
        elif "interested" in text or "sounds good" in text or "book" in text:
            classification = {"intent": "interested", "confidence": 0.93, "requires_human_review": False, "sentiment": "positive"}
        elif "not interested" in text:
            classification = {
                "intent": "not_interested",
                "confidence": 0.95,
                "requires_human_review": False,
                "sentiment": "negative",
            }
        elif "out of office" in text:
            classification = {
                "intent": "out_of_office",
                "confidence": 0.97,
                "requires_human_review": False,
                "sentiment": "neutral",
            }
        elif "next quarter" in text or "later" in text:
            classification = {"intent": "not_now", "confidence": 0.76, "requires_human_review": True, "sentiment": "neutral"}
        elif "who handles" in text or "reach out to" in text:
            classification = {"intent": "referral", "confidence": 0.82, "requires_human_review": True, "sentiment": "neutral"}
        elif "?" in text:
            classification = {"intent": "question", "confidence": 0.74, "requires_human_review": True, "sentiment": "neutral"}

        parsed = parse_json_object(json.dumps(classification), fallback=classification)
        return ReplyClassificationResult(
            intent=str(parsed.get("intent", "unknown")),
            confidence=clamp_score(parsed.get("confidence"), default=0.55),
            requires_human_review=bool(parsed.get("requires_human_review", True)),
            sentiment=str(parsed.get("sentiment", "neutral")),
        )

    def generate_booking_response(self, lead_name: str) -> str:
        return (
            f"Hi {lead_name},\n\nGreat to connect. I can hold 30 minutes this week. "
            "Would Tuesday or Thursday morning work best?\n\nBest,\nThorpe Workforce"
        )

    def execute_worker(
        self,
        *,
        model_name: str,
        prompt: str,
        tools: list[str],
        runtime_input: dict[str, Any],
        context: dict[str, Any],
    ) -> WorkerModelResponse:
        preferred_tool = tools[0] if tools else None
        output: dict[str, Any] = {
            "summary": "Worker instance executed successfully with structured output.",
            "output": {
                "mission_status": "completed",
                "runtime_echo": runtime_input,
                "capability_count": len(context.get("capabilities", {})) if isinstance(context.get("capabilities"), dict) else 0,
            },
            "tool_calls": [],
            "memory_updates": {},
        }
        if preferred_tool:
            output["tool_calls"].append({"tool": preferred_tool, "input": {"source": "mock"}})
        # Include one invalid tool call so the execution layer can verify suppression.
        output["tool_calls"].append({"tool": "disallowed_tool", "input": {"source": "mock"}})
        output["memory_updates"] = {"last_runtime_input": runtime_input}

        input_tokens = max(len(prompt) // 4, 1)
        output_tokens = max(len(json.dumps(output)) // 4, 1)
        return WorkerModelResponse(
            text=json.dumps(output),
            model=model_name or "mock-ai-v1",
            token_usage_input=input_tokens,
            token_usage_output=output_tokens,
            cost_cents=max((input_tokens + output_tokens) // 200, 1),
            metadata={"provider": "mock", "tool_count": len(tools)},
        )
