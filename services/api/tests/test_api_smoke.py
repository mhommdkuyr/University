from fastapi.testclient import TestClient

from app.core.access_control import AccessPolicy, Permission, PlatformRole, StudentStatus
from app.main import app


client = TestClient(app)


def login(email: str, password: str):
    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password, "tenant_id": "demo"},
    )
    assert response.status_code == 200, response.text
    return response.json()["access_token"]


def test_health_is_live():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"
    assert response.json()["database"] == "ok"


def test_openapi_is_available():
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()


def test_public_projects_are_tenant_aware():
    response = client.get("/api/v1/projects/", headers={"X-Tenant-ID": "demo"})
    assert response.status_code == 200
    body = response.json()
    assert body and body[0]["slug"] == "smart-multi-tenant-cloud-core"


def test_login_returns_signed_token_and_identity_is_scoped():
    token = login("student@demo.edu", "DemoStudent123!")
    response = client.get(
        "/api/v1/identity/me",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": "demo"},
    )
    assert response.status_code == 200
    assert response.json()["student_number"] == "DEMO-1001"
    assert response.json()["role"] == "student"


def test_student_cannot_write_attendance():
    token = login("student@demo.edu", "DemoStudent123!")
    response = client.post(
        "/api/v1/teaching/attendance",
        headers={"Authorization": f"Bearer {token}"},
        json=[{"student_id": "demo-student", "course_id": "course-swe-432", "present": True}],
    )
    assert response.status_code == 403


def test_student_ai_gate_is_authorized_but_provider_can_be_disabled():
    token = login("student@demo.edu", "DemoStudent123!")
    response = client.post(
        "/api/v1/ai/execute",
        headers={"Authorization": f"Bearer {token}"},
        json={"prompt": "اشرح لي المقرر"},
    )
    assert response.status_code == 200
    assert "مصرح" in response.json()["response_text"]


def test_president_can_create_group():
    token = login("president@demo.edu", "DemoPresident123!")
    response = client.post(
        "/api/v1/teaching/groups",
        headers={"Authorization": f"Bearer {token}"},
        json={"course_id": "course-swe-432", "name": "Group A", "student_ids": ["demo-student"]},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Group A"


def test_access_policy_removes_private_student_capabilities():
    policy = AccessPolicy()
    context = policy.build_context(
        tenant_id="demo",
        user_id="student-1",
        role=PlatformRole.STUDENT,
        student_status=StudentStatus.GRADUATED,
    )
    assert Permission.USE_AI not in context.permissions
    assert Permission.VIEW_ACADEMICS not in context.permissions
    assert Permission.COURSE_ENROLL not in context.permissions
