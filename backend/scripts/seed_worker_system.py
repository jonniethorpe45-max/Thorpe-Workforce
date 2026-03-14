import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.db.session import SessionLocal
from app.services.system_seed import seed_system_worker_templates_and_tools


def seed() -> None:
    db = SessionLocal()
    try:
        summary = seed_system_worker_templates_and_tools(db)
        db.commit()
        print("Ensured system worker templates and common worker tools.")
        print(f"Templates created: {summary.templates_created}")
        print(f"Tools created: {summary.tools_created}")
        print(f"Subscription plans ensured: {summary.plans_upserted}")
        print(f"Templates available: {', '.join(summary.template_names)}")
        print(f"Common tools available: {', '.join(summary.common_tool_slugs)}")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
