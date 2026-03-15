from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


def _read_root_file(name: str) -> str:
    root = Path(__file__).resolve().parents[2]
    return (root / name).read_text(encoding="utf-8")


def test_local_compose_contains_full_stack_services():
    compose = _read_root_file("docker-compose.yml")
    for token in [
        "postgres:",
        "redis:",
        "backend:",
        "frontend:",
        "worker-runner:",
        "8000:8000",
        "3000:3000",
        "scripts/bootstrap_runtime.py",
    ]:
        assert token in compose


def test_production_compose_and_dockerfiles_exist():
    root = Path(__file__).resolve().parents[2]
    assert (root / "docker-compose.production.yml").exists()
    assert (root / "Dockerfile.backend").exists()
    assert (root / "Dockerfile.frontend").exists()
    assert (root / "scripts" / "start_local.sh").exists()
    assert (root / "scripts" / "reset_local.sh").exists()
    assert (root / "scripts" / "deploy_production.sh").exists()
    assert (root / "backend" / "railway.json").exists()
    assert (root / "backend" / "Procfile").exists()


def test_backend_start_script_uses_platform_port():
    root = Path(__file__).resolve().parents[2]
    script = (root / "backend" / "scripts" / "start_production.sh").read_text(encoding="utf-8")
    assert "PORT" in script
    assert "0.0.0.0" in script


def test_alembic_head_revision_matches_latest_founder_os_migration():
    backend_root = Path(__file__).resolve().parents[1]
    alembic_cfg = Config(str(backend_root / "alembic.ini"))
    script = ScriptDirectory.from_config(alembic_cfg)
    assert script.get_current_head() == "0010_founder_os_layer"
