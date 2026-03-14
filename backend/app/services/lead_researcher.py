from sqlalchemy.orm import Session

from app.models import CompanyResearch, Lead, LeadStatus
from app.services.ai_service import generate_company_research


def research_lead(db: Session, lead: Lead) -> CompanyResearch:
    result = generate_company_research(company_name=lead.company_name, website=lead.website, industry=lead.lead_source)
    existing = db.query(CompanyResearch).filter(CompanyResearch.lead_id == lead.id).first()
    if existing:
        existing.summary = result.summary
        existing.pain_points = result.pain_points
        existing.relevance_score = result.relevance_score
        existing.personalization_hook = result.personalization_hook
        existing.generated_by_model = result.model
        lead.lead_status = LeadStatus.READY_FOR_OUTREACH.value
        return existing
    research = CompanyResearch(
        lead_id=lead.id,
        summary=result.summary,
        pain_points=result.pain_points,
        relevance_score=result.relevance_score,
        personalization_hook=result.personalization_hook,
        generated_by_model=result.model,
    )
    lead.lead_status = LeadStatus.READY_FOR_OUTREACH.value
    db.add(research)
    return research
