from app.integrations.ai.factory import get_ai_provider


def generate_company_research(company_name: str, website: str | None, industry: str | None):
    return get_ai_provider().generate_company_research(company_name=company_name, website=website, industry=industry)


def generate_outreach_email(lead_name: str, company_name: str, title: str | None, cta: str):
    return get_ai_provider().generate_outreach_email(
        lead_name=lead_name,
        company_name=company_name,
        title=title,
        cta=cta,
    )


def generate_followup_email(lead_name: str, company_name: str, step: int, cta: str):
    return get_ai_provider().generate_followup_email(
        lead_name=lead_name,
        company_name=company_name,
        step=step,
        cta=cta,
    )


def classify_reply(reply_text: str):
    return get_ai_provider().classify_reply(reply_text=reply_text)


def generate_booking_response(lead_name: str):
    return get_ai_provider().generate_booking_response(lead_name=lead_name)
