from datetime import UTC, datetime, timedelta

from sqlalchemy.orm import Session

from app.models import EmailSequence, GeneratedMessage


def schedule_followups(db: Session, campaign_id) -> list[dict]:
    sequence_steps = (
        db.query(EmailSequence)
        .filter(EmailSequence.campaign_id == campaign_id)
        .order_by(EmailSequence.step_order.asc())
        .all()
    )
    if not sequence_steps:
        return []
    generated = db.query(GeneratedMessage).filter(GeneratedMessage.campaign_id == campaign_id).all()
    schedule = []
    now = datetime.now(UTC)
    for item in generated:
        step_cfg = next((s for s in sequence_steps if s.step_order == item.sequence_step), None)
        delay = step_cfg.delay_days if step_cfg else max(item.sequence_step - 1, 0) * 3
        schedule.append({"generated_message_id": str(item.id), "scheduled_for": (now + timedelta(days=delay)).isoformat()})
    return schedule
