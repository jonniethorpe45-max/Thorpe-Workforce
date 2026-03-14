from app.integrations.ai.base import (
    AIProvider,
    CompanyResearchResult,
    OutreachEmailResult,
    ReplyClassificationResult,
)


class MockAIProvider(AIProvider):
    def generate_company_research(self, company_name: str, website: str | None, industry: str | None) -> CompanyResearchResult:
        summary = f"{company_name} appears to be a growing organization focused on operational efficiency."
        if website:
            summary += f" Public website signals include {website} and a modern digital presence."
        pain_points = [
            "Pipeline inconsistency across reps",
            "Slow follow-up cadence causing lead decay",
            "Limited personalization at scale",
        ]
        hook = f"Noticed {company_name}'s momentum in {industry or 'their market'} and thought this could support outbound scale."
        return CompanyResearchResult(
            summary=summary,
            pain_points=pain_points,
            relevance_score=0.82,
            personalization_hook=hook,
            model="mock-ai-v1",
        )

    def generate_outreach_email(self, lead_name: str, company_name: str, title: str | None, cta: str) -> OutreachEmailResult:
        subject = f"Idea for {company_name}'s outbound pipeline"
        body = (
            f"Hi {lead_name},\n\n"
            f"I work with teams like {company_name} to improve outbound consistency without adding headcount. "
            f"I noticed your role in {title or 'revenue operations'} and thought this might be timely.\n\n"
            f"{cta}\n\n"
            "Best,\nThorpe Workforce"
        )
        return OutreachEmailResult(subject=subject, body=body, personalization={"type": "role_context"})

    def generate_followup_email(self, lead_name: str, company_name: str, step: int, cta: str) -> OutreachEmailResult:
        subject = f"Quick follow-up on outbound at {company_name}"
        body = (
            f"Hi {lead_name},\n\n"
            f"Following up on my previous note. Step {step} of outreach is usually where teams ask for concrete examples. "
            f"Thorpe Workforce can auto-research leads, draft high-signal emails, and manage follow-up timing.\n\n"
            f"{cta}\n\n"
            "Regards,\nThorpe Workforce"
        )
        return OutreachEmailResult(subject=subject, body=body, personalization={"step": step})

    def classify_reply(self, reply_text: str) -> ReplyClassificationResult:
        text = reply_text.lower()
        if "unsubscribe" in text:
            return ReplyClassificationResult("unsubscribe", 0.99, False, "neutral")
        if "interested" in text or "sounds good" in text or "book" in text:
            return ReplyClassificationResult("interested", 0.93, False, "positive")
        if "not interested" in text:
            return ReplyClassificationResult("not_interested", 0.95, False, "negative")
        if "out of office" in text:
            return ReplyClassificationResult("out_of_office", 0.97, False, "neutral")
        if "next quarter" in text or "later" in text:
            return ReplyClassificationResult("not_now", 0.76, True, "neutral")
        if "who handles" in text or "reach out to" in text:
            return ReplyClassificationResult("referral", 0.82, True, "neutral")
        if "?" in text:
            return ReplyClassificationResult("question", 0.74, True, "neutral")
        return ReplyClassificationResult("unknown", 0.55, True, "neutral")

    def generate_booking_response(self, lead_name: str) -> str:
        return (
            f"Hi {lead_name},\n\nGreat to connect. I can hold 30 minutes this week. "
            "Would Tuesday or Thursday morning work best?\n\nBest,\nThorpe Workforce"
        )
