import httpx

from app.integrations.frappe_education import FrappeEducationClient, FrappeEducationConfig


def test_frappe_student_lookup_uses_token_auth():
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(
            200,
            json={
                "data": [
                    {
                        "name": "STD-001",
                        "student_number": "DEMO-1001",
                        "student_name": "Demo Student",
                        "enabled": 1,
                    }
                ]
            },
            request=request,
        )

    transport = httpx.MockTransport(handler)
    config = FrappeEducationConfig(
        base_url="https://frappe.example.edu",
        api_key="demo-key",
        api_secret="demo-secret",
    )
    client = FrappeEducationClient(config, transport=transport)

    import asyncio

    student = asyncio.run(client.find_student_by_number("DEMO-1001"))
    assert student["name"] == "STD-001"
    assert requests[0].headers["Authorization"] == "token demo-key:demo-secret"
    assert "filters=" in str(requests[0].url)
