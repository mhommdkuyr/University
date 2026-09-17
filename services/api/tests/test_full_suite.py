import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["architecture"] == "Modular Monolith"

def test_tenant_middleware_enforcement():
    # Calling private endpoint without X-Tenant-ID header should fail
    response = client.get("/api/v1/academics/courses")
    assert response.status_code == 400
    assert "Tenant identification missing" in response.json()["detail"]

def test_tenant_middleware_with_header():
    response = client.get("/api/v1/academics/courses", headers={"X-Tenant-ID": "test-university"})
    assert response.status_code == 200
    courses = response.json()
    assert isinstance(courses, list)
    assert len(courses) > 0

def test_auth_login_endpoint():
    response = client.post(
        "/api/v1/auth/login",
        json={"student_id": "STD-99001"},
        headers={"X-Tenant-ID": "test-university"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "test-university"
    assert data["role"] == "student"

def test_billing_and_commercial():
    response = client.get("/api/v1/commercial/billing/usage", headers={"X-Tenant-ID": "test-university"})
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "test-university"
    assert "active_students_count" in data
