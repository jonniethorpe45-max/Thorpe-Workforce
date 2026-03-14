from app.integrations.ai.factory import get_ai_provider
from app.integrations.ai.base import CompanyResearchResult, OutreachEmailResult, ReplyClassificationResult
from app.services.ai_utils import clamp_score, enforce_single_cta, enforce_word_limit, normalize_whitespace, sanitize_list


def generate_company_research(company_name: str, website: str | None, industry: str | None):
    result = get_ai_provider().generate_company_research(company_name=company_name, website=website, industry=industry)
    return CompanyResearchResult(
        summary=normalize_whitespace(result.summary) or f"{company_name} appears to be a fit for outbound optimization.",
        pain_points=sanitize_list(result.pain_points) or ["Outbound inconsistency", "Manual personalization limits"],
        relevance_score=clamp_score(result.relevance_score, default=0.65),
        personalization_hook=normalize_whitespace(result.personalization_hook)
        or f"Thought this could help {company_name} run more consistent outbound.",
        model=result.model or "unknown-model",
    )


def generate_outreach_email(lead_name: str, company_name: str, title: str | None, cta: str):
    result = get_ai_provider().generate_outreach_email(
        lead_name=lead_name,
        company_name=company_name,
        title=title,
        cta=cta,
    )
    body = enforce_single_cta(enforce_word_limit(result.body, max_words=120), cta)
    return OutreachEmailResult(
        subject=normalize_whitespace(result.subject) or f"Quick idea for {company_name}",
        body=body,
        personalization=result.personalization if isinstance(result.personalization, dict) else {},
    )


def generate_followup_email(lead_name: str, company_name: str, step: int, cta: str):
    result = get_ai_provider().generate_followup_email(
        lead_name=lead_name,
        company_name=company_name,
        step=step,
        cta=cta,
    )
    body = enforce_single_cta(enforce_word_limit(result.body, max_words=120), cta)
    return OutreachEmailResult(
        subject=normalize_whitespace(result.subject) or f"Quick follow-up for {company_name}",
        body=body,
        personalization=result.personalization if isinstance(result.personalization, dict) else {"step": step},
    )


def classify_reply(reply_text: str):
    result = get_ai_provider().classify_reply(reply_text=reply_text)
    return ReplyClassificationResult(
        intent=normalize_whitespace(result.intent) or "unknown",
        confidence=clamp_score(result.confidence, default=0.5),
        requires_human_review=bool(result.requires_human_review),
        sentiment=normalize_whitespace(result.sentiment) or "neutral",
    )


def generate_booking_response(lead_name: str):
    return get_ai_provider().generate_booking_response(lead_name=lead_name)
