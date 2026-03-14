import os
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ["DATABASE_URL"] = "sqlite:///./test.db"
os.environ["INTERNAL_WORKER_BUILDER_ENABLED"] = "true"
os.environ["ENVIRONMENT"] = "test"

from app.db.base import Base  # noqa: E402
from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models import *  # noqa: E402,F401,F403
from app.core.rate_limit import _request_buckets  # noqa: E402

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_database():
    _request_buckets.clear()
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    _request_buckets.clear()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def auth_headers(client: TestClient):
    signup_payload = {
        "full_name": "Tester",
        "email": "tester@example.com",
        "password": "Passw0rd!",
        "company_name": "TestCo",
        "website": "https://test.co",
        "industry": "SaaS",
    }
    res = client.post("/auth/signup", json=signup_payload)
    token = res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
