"""
Integration tests run against a real PostgreSQL database
(tesseractis_test), not sqlite/mocks — so these catch real
migration/ORM/constraint issues, not just Python-level logic bugs.
"""
import io
import os
import uuid

import pytest
from fastapi.testclient import TestClient
from PIL import Image
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg2://tesseractis:tesseractis@localhost:5432/tesseractis_test")
os.environ.setdefault("AI_PROVIDER", "mock")

from app.core.config import get_settings  # noqa: E402
from app.core.db import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

settings = get_settings()
engine = create_engine(settings.DATABASE_URL)
TestSessionLocal = sessionmaker(bind=engine)


@pytest.fixture(scope="module", autouse=True)
def _setup_schema():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture()
def db_session():
    session = TestSessionLocal()
    yield session
    session.close()


@pytest.fixture(autouse=True)
def _reset_rate_limits():
    """Each test gets a clean rate-limit slate. In production this window
    is exactly what protects real users; in tests it must not cause
    unrelated tests to fail each other via shared TestClient IP."""
    from app.security.rate_limit import get_redis

    get_redis().flushdb()
    yield


@pytest.fixture()
def client(db_session):
    def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def _jpeg_bytes() -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", (200, 200), color=(80, 120, 200)).save(buf, format="JPEG")
    return buf.getvalue()


def _register(client: TestClient, email: str, password: str = "correcthorse123") -> TestClient:
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    return resp


def test_register_login_me_flow(client):
    email = f"user_{uuid.uuid4().hex[:8]}@example.com"
    resp = _register(client, email)
    assert resp.json()["email"] == email

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == email


def test_duplicate_registration_rejected(client):
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email)
    resp2 = client.post("/api/v1/auth/register", json={"email": email, "password": "correcthorse123"})
    assert resp2.status_code == 400


def test_weak_password_rejected(client):
    email = f"weak_{uuid.uuid4().hex[:8]}@example.com"
    resp = client.post("/api/v1/auth/register", json={"email": email, "password": "abc"})
    assert resp.status_code == 422  # pydantic validation error


def test_login_wrong_password_rejected(client):
    email = f"login_{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email, password="correcthorse123")
    client.post("/api/v1/auth/logout")
    resp = client.post("/api/v1/auth/login", json={"email": email, "password": "wrongpassword1"})
    assert resp.status_code == 401


def test_unauthenticated_cannot_access_me(client):
    resp = client.get("/api/v1/auth/me")
    assert resp.status_code == 401


def test_upload_analyze_and_history_flow(client):
    _register(client, f"scan_{uuid.uuid4().hex[:8]}@example.com")
    files = {"file": ("photo.jpg", _jpeg_bytes(), "image/jpeg")}
    resp = client.post("/api/v1/scans", files=files)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["status"] == "completed"
    assert 0.0 <= body["overall_confidence"] <= 1.0
    assert body["is_mock_result"] is True  # never disguise mock as real

    scan_id = body["id"]
    detail = client.get(f"/api/v1/scans/{scan_id}")
    assert detail.status_code == 200

    history = client.get("/api/v1/scans")
    assert history.status_code == 200
    assert any(s["id"] == scan_id for s in history.json())


def test_malformed_image_rejected(client):
    _register(client, f"bad_{uuid.uuid4().hex[:8]}@example.com")
    files = {"file": ("fake.jpg", b"not a real image at all", "image/jpeg")}
    resp = client.post("/api/v1/scans", files=files)
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "UNSUPPORTED_FORMAT"


def test_cross_user_scan_access_denied(client, db_session):
    """The single most important security test in this suite: User A's
    data must be completely inaccessible to User B."""
    client_a = client
    _register(client_a, f"alice_{uuid.uuid4().hex[:8]}@example.com")
    files = {"file": ("photo.jpg", _jpeg_bytes(), "image/jpeg")}
    scan_resp = client_a.post("/api/v1/scans", files=files)
    scan_id = scan_resp.json()["id"]

    client_a.post("/api/v1/auth/logout")
    _register(client_a, f"bob_{uuid.uuid4().hex[:8]}@example.com")

    resp = client_a.get(f"/api/v1/scans/{scan_id}")
    assert resp.status_code == 403

    resp_del = client_a.delete(f"/api/v1/scans/{scan_id}")
    assert resp_del.status_code == 403


def test_non_admin_cannot_access_admin_routes(client):
    _register(client, f"plain_{uuid.uuid4().hex[:8]}@example.com")
    resp = client.get("/api/v1/admin/analytics")
    assert resp.status_code == 403


def test_admin_analytics_reflects_real_counts(client, db_session):
    from app.models.core import User, UserRole

    email = f"admin_{uuid.uuid4().hex[:8]}@example.com"
    _register(client, email)
    user = db_session.query(User).filter(User.email == email).first()
    user.role = UserRole.ADMIN
    db_session.commit()

    resp = client.get("/api/v1/admin/analytics")
    assert resp.status_code == 200
    body = resp.json()
    assert body["data_source"] == "live_database"
    assert body["total_users"] >= 1
