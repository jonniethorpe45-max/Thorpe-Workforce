import uuid
from datetime import UTC, datetime, timedelta

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models import (
    ApprovalStatus,
    AuditLog,
    Campaign,
    CompanyResearch,
    GeneratedMessage,
    Lead,
    LeadStatus,
    Meeting,
    Reply,
    SentEmail,
    User,
    Worker,
    WorkerRun,
    Workspace,
)
from app.services.system_seed import seed_system_worker_templates_and_tools


def seed() -> None:
    db = SessionLocal()
    try:
        system_seed_summary = seed_system_worker_templates_and_tools(db)
        db.commit()
        print(
            "Ensured system worker templates/tools "
            f"(templates_created={system_seed_summary.templates_created}, "
            f"tools_created={system_seed_summary.tools_created})."
        )

        existing = db.query(User).filter(User.email == "demo@thorpeworkforce.com").first()
        if existing:
            print("Demo data already exists.")
            return

        workspace = Workspace(
            id=uuid.uuid4(),
            company_name="Acme Growth Labs",
            website="https://acmegrowthlabs.com",
            industry="B2B SaaS",
            subscription_plan="pro",
        )
        db.add(workspace)
        db.flush()

        user = User(
            workspace_id=workspace.id,
            full_name="Demo Admin",
            email="demo@thorpeworkforce.com",
            password_hash=hash_password("DemoPass123!"),
            role="owner",
        )
        db.add(user)

        worker = Worker(
            workspace_id=workspace.id,
            name="Outbound SDR Alpha",
            worker_type="ai_sales_worker",
            worker_category="go_to_market",
            mission="Book 10 qualified pipeline meetings per month.",
            goal="Book 10 qualified pipeline meetings per month.",
            plan_version="sales_v1",
            allowed_actions=[
                "select_eligible_leads",
                "research_selected_leads",
                "generate_messages_for_selected_leads",
                "dispatch_messages",
                "monitor_outbound_events",
                "record_optimization_signals",
            ],
            origin_type="built_in",
            is_custom_worker=False,
            is_internal=False,
            status="monitoring",
            tone="professional",
            send_limit_per_day=45,
            config_json={
                "target_industry": "B2B SaaS",
                "target_roles": ["VP Sales", "Head of Growth", "Revenue Operations"],
                "target_locations": ["United States", "Canada"],
                "company_size_range": "50-500",
            },
        )
        db.add(worker)
        db.flush()

        campaign = Campaign(
            workspace_id=workspace.id,
            worker_id=worker.id,
            name="Q2 Pipeline Builder",
            target_industry="B2B SaaS",
            target_roles=["VP Sales", "Head of Growth"],
            target_locations=["US", "Canada"],
            company_size_min=50,
            company_size_max=500,
            cta_text="Would you be open to a 15-minute intro next week?",
            status="active",
        )
        db.add(campaign)
        db.flush()

        leads = [
            Lead(
                workspace_id=workspace.id,
                campaign_id=campaign.id,
                company_name="Nimbus AI",
                website="https://nimbus.ai",
                first_name="Jordan",
                last_name="Lee",
                full_name="Jordan Lee",
                title="VP Sales",
                email="jordan@nimbus.ai",
                linkedin_url="https://linkedin.com/in/jordanlee",
                location="San Francisco, CA",
                company_size=220,
                lead_source="manual_import",
                lead_status=LeadStatus.CONTACTED.value,
                enrichment_json={"tech_stack": ["HubSpot", "Apollo"]},
            ),
            Lead(
                workspace_id=workspace.id,
                campaign_id=campaign.id,
                company_name="Stackline Data",
                website="https://stackline.example",
                first_name="Priya",
                last_name="Patel",
                full_name="Priya Patel",
                title="Head of Growth",
                email="priya@stackline.example",
                location="New York, NY",
                company_size=130,
                lead_source="manual_import",
                lead_status=LeadStatus.REPLIED_POSITIVE.value,
                enrichment_json={"intent_signal": "hiring SDR team"},
            ),
            Lead(
                workspace_id=workspace.id,
                campaign_id=campaign.id,
                company_name="Mosaic Ops",
                website="https://mosaicops.example",
                first_name="Daniel",
                last_name="Reyes",
                full_name="Daniel Reyes",
                title="Revenue Operations Lead",
                email="daniel@mosaicops.example",
                location="Austin, TX",
                company_size=85,
                lead_source="manual_import",
                lead_status=LeadStatus.READY_FOR_OUTREACH.value,
                enrichment_json={"priority": "high"},
            ),
        ]
        db.add_all(leads)
        db.flush()

        for lead in leads:
            db.add(
                CompanyResearch(
                    lead_id=lead.id,
                    summary=f"{lead.company_name} is scaling GTM and likely needs repeatable outbound coverage.",
                    pain_points=[
                        "Inconsistent outreach volume",
                        "Limited personalization bandwidth",
                        "Slow lead response SLAs",
                    ],
                    relevance_score=0.84,
                    personalization_hook=f"Noticed {lead.company_name}'s growth momentum in their go-to-market team.",
                    generated_by_model="mock-ai-v1",
                )
            )

        generated = GeneratedMessage(
            campaign_id=campaign.id,
            lead_id=leads[0].id,
            sequence_step=1,
            subject_line="Idea to scale outbound at Nimbus AI",
            body_text="Hi Jordan, we help teams run personalized outbound with less manual lift. Open to a quick intro call?",
            personalization_json={"hook": "sales team scaling"},
            approval_status=ApprovalStatus.APPROVED.value,
        )
        db.add(generated)
        db.flush()

        sent = SentEmail(
            workspace_id=workspace.id,
            campaign_id=campaign.id,
            lead_id=leads[0].id,
            generated_message_id=generated.id,
            provider_message_id="seed-msg-001",
            sent_at=datetime.now(UTC) - timedelta(days=2),
            delivery_status="delivered",
            open_count=2,
            click_count=1,
            reply_detected=True,
            bounce_detected=False,
            unsubscribed=False,
        )
        db.add(sent)
        db.flush()

        db.add(
            Reply(
                sent_email_id=sent.id,
                lead_id=leads[0].id,
                reply_text="This looks interesting, can we talk next week?",
                sentiment="positive",
                intent_classification="interested",
                requires_human_review=False,
            )
        )

        db.add(
            Meeting(
                workspace_id=workspace.id,
                campaign_id=campaign.id,
                lead_id=leads[1].id,
                calendar_provider="google",
                external_event_id="seed-event-001",
                scheduled_start=datetime.now(UTC) + timedelta(days=3),
                scheduled_end=datetime.now(UTC) + timedelta(days=3, minutes=30),
                meeting_status="scheduled",
            )
        )

        db.add(
            WorkerRun(
                worker_id=worker.id,
                run_type="worker_execution",
                status="completed",
                input_json={"campaign_id": str(campaign.id), "worker_type": "ai_sales_worker"},
                output_json={"leads_processed": 3, "emails_sent": 1},
                error_text=None,
            )
        )

        db.add_all(
            [
                AuditLog(
                    workspace_id=workspace.id,
                    actor_type="system",
                    actor_id="seed",
                    event_name="seed_initialized",
                    payload_json={"workspace": workspace.company_name},
                ),
                AuditLog(
                    workspace_id=workspace.id,
                    actor_type="user",
                    actor_id=str(user.id),
                    event_name="campaign_launched",
                    payload_json={"campaign_id": str(campaign.id)},
                ),
            ]
        )

        db.commit()
        print("Seeded demo data.")
        print("Demo login: demo@thorpeworkforce.com / DemoPass123!")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
