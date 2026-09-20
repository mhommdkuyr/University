from fastapi.testclient import TestClient

from app.core.access_control import AccessPolicy, Permission, PlatformRole, StudentStatus
from app.main import app


client = TestClient(app)


def test_health_is_live():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "online"


def test_openapi_is_available():
    response = client.get("/api/v1/openapi.json")
    assert response.status_code == 200
    assert "paths" in response.json()


def test_public_projects_are_tenant_aware():
    response = client.get("/api/v1/projects/", headers={"X-Tenant-ID": "demo-university"})
    assert response.status_code == 200
    body = response.json()
    assert body and body[0]["public_url"].startswith("https://demo-university.")


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
