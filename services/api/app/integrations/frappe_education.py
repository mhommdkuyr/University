from __future__ import annotations

import json
import os
from dataclasses import dataclass

import httpx


@dataclass(frozen=True)
class FrappeEducationConfig:
    base_url: str
    api_key: str
    api_secret: str
    student_number_field: str = "student_number"

    @classmethod
    def from_env(cls) -> "FrappeEducationConfig":
        return cls(
            base_url=os.getenv("FRAPPE_EDUCATION_BASE_URL", "").rstrip("/"),
            api_key=os.getenv("FRAPPE_EDUCATION_API_KEY", ""),
            api_secret=os.getenv("FRAPPE_EDUCATION_API_SECRET", ""),
            student_number_field=os.getenv("FRAPPE_EDUCATION_STUDENT_NUMBER_FIELD", "student_number"),
        )

    @property
    def enabled(self) -> bool:
        return bool(self.base_url and self.api_key and self.api_secret)


class FrappeEducationClient:
    def __init__(self, config: FrappeEducationConfig | None = None, transport: httpx.AsyncBaseTransport | None = None):
        self.config = config or FrappeEducationConfig.from_env()
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        return {
            "Authorization": f"token {self.config.api_key}:{self.config.api_secret}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    async def health(self) -> bool:
        if not self.config.enabled:
            return False
        async with httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=self._headers(),
            timeout=15,
            transport=self.transport,
        ) as client:
            response = await client.get("/api/method/frappe.auth.get_logged_user")
            response.raise_for_status()
            return True

    async def list_students(self, limit: int = 100) -> list[dict]:
        if not self.config.enabled:
            raise RuntimeError("Frappe Education connector is not configured")
        params = {
            "fields": json.dumps(["name", self.config.student_number_field, "student_name", "enabled"]),
            "limit_page_length": min(max(limit, 1), 500),
        }
        async with httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=self._headers(),
            timeout=20,
            transport=self.transport,
        ) as client:
            response = await client.get("/api/resource/Student", params=params)
            response.raise_for_status()
            return response.json().get("data", [])

    async def find_student_by_number(self, student_number: str) -> dict | None:
        if not self.config.enabled:
            raise RuntimeError("Frappe Education connector is not configured")
        filters = [[
            "Student",
            self.config.student_number_field,
            "=",
            student_number,
        ]]
        params = {
            "fields": json.dumps(["name", self.config.student_number_field, "student_name", "enabled"]),
            "filters": json.dumps(filters),
            "limit_page_length": 1,
        }
        async with httpx.AsyncClient(
            base_url=self.config.base_url,
            headers=self._headers(),
            timeout=15,
            transport=self.transport,
        ) as client:
            response = await client.get("/api/resource/Student", params=params)
            response.raise_for_status()
            rows = response.json().get("data", [])
            return rows[0] if rows else None
