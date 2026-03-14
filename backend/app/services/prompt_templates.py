def company_research_prompt(company_name: str, website: str | None, industry: str | None) -> str:
    return (
        "You are an AI sales researcher. Return strict JSON with keys "
        '{"summary": string, "pain_points": string[], "relevance_score": number, "personalization_hook": string}. '
        f"Company: {company_name}. Website: {website or 'unknown'}. Industry: {industry or 'unknown'}."
    )


def outreach_prompt(lead_name: str, company_name: str, title: str | None, cta: str) -> str:
    return (
        "You are an AI Sales Worker drafting a first outbound email. Return strict JSON "
        '{"subject": string, "body": string, "personalization": object}. '
        "Constraints: <=120 words, grounded only in known data, one clear CTA. "
        f"Lead: {lead_name}. Company: {company_name}. Role: {title or 'unknown'}. CTA: {cta}."
    )


def followup_prompt(lead_name: str, company_name: str, step: int, cta: str) -> str:
    return (
        "You are an AI Sales Worker drafting a follow-up email. Return strict JSON "
        '{"subject": string, "body": string, "personalization": object}. '
        "Constraints: concise, professional, one CTA. "
        f"Lead: {lead_name}. Company: {company_name}. Follow-up step: {step}. CTA: {cta}."
    )


def reply_classification_prompt(reply_text: str) -> str:
    return (
        "Classify this reply into one of "
        "[interested, not_now, not_interested, referral, question, unsubscribe, out_of_office, unknown]. "
        "Return strict JSON with keys "
        '{"intent": string, "confidence": number, "requires_human_review": boolean, "sentiment": string}. '
        f"Reply text: {reply_text}"
    )
