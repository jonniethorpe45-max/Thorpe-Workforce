import csv
import io
from typing import Iterable

from sqlalchemy.orm import Session

from app.models import Lead, LeadStatus
from app.schemas.api import LeadCreate


def import_leads_from_rows(db: Session, workspace_id, rows: Iterable[dict], campaign_id=None) -> dict:
    created = 0
    skipped_duplicates = 0
    seen_batch_emails: set[str] = set()
    for row in rows:
        email = (row.get("email") or "").strip().lower()
        company_name = (row.get("company_name") or "").strip()
        if not email or not company_name:
            continue
        if email in seen_batch_emails:
            skipped_duplicates += 1
            continue
        existing = db.query(Lead).filter(Lead.workspace_id == workspace_id, Lead.email == email).first()
        if existing:
            skipped_duplicates += 1
            continue
        lead = Lead(
            workspace_id=workspace_id,
            campaign_id=campaign_id,
            company_name=company_name,
            website=row.get("website"),
            first_name=row.get("first_name"),
            last_name=row.get("last_name"),
            full_name=row.get("full_name"),
            title=row.get("title"),
            email=email,
            linkedin_url=row.get("linkedin_url"),
            location=row.get("location"),
            company_size=int(row["company_size"]) if row.get("company_size") else None,
            lead_source=row.get("lead_source", "manual_import"),
            lead_status=LeadStatus.NEW.value,
            enrichment_json={},
        )
        db.add(lead)
        seen_batch_emails.add(email)
        created += 1
    return {"created": created, "skipped_duplicates": skipped_duplicates}


def parse_csv_bytes(content: bytes) -> list[dict]:
    text = content.decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def create_single_lead(db: Session, workspace_id, payload: LeadCreate) -> Lead:
    existing = db.query(Lead).filter(Lead.workspace_id == workspace_id, Lead.email == payload.email.lower()).first()
    if existing:
        return existing
    lead = Lead(
        workspace_id=workspace_id,
        campaign_id=payload.campaign_id,
        company_name=payload.company_name,
        website=payload.website,
        first_name=payload.first_name,
        last_name=payload.last_name,
        full_name=payload.full_name,
        title=payload.title,
        email=payload.email.lower(),
        linkedin_url=payload.linkedin_url,
        location=payload.location,
        company_size=payload.company_size,
        lead_source=payload.lead_source or "manual_form",
        lead_status=LeadStatus.NEW.value,
        enrichment_json=payload.enrichment_json or {},
    )
    db.add(lead)
    return lead
