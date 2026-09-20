from __future__ import annotations

from typing import Any
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import AccessPolicy, Permission, request_access_context
from app.core.config import settings
from app.core.rate_limit import limiter
from app.core.database import AuditLog, SessionLocal
from app.modules.access.service import AuthorizationService


router = APIRouter()
_access = AccessPolicy()
_authorization = AuthorizationService()


class AgentRequest(BaseModel):
    prompt: str = Field(min_length=1, max_length=12_000)
    user_role: str = "student"


class AgentResponse(BaseModel):
    intent: str
    action_type: str
    requires_confirmation: bool
    confirmation_payload: dict[str, Any] | None = None
    response_text: str


def _model_candidates() -> list[str]:
    values = [settings.AI_MODEL]
    values.extend(item.strip() for item in settings.AI_FALLBACK_MODELS.split(",") if item.strip())
    return list(dict.fromkeys(values))


@router.post("/execute", response_model=AgentResponse)
async def execute_agent_command(request: Request, payload: AgentRequest):
    context = request_access_context(request)
    _access.require_active_student(context)
    _access.require(context, Permission.USE_AI)

    tenant_id = context.tenant_id
    allowed = await limiter.allow(f"ai:{tenant_id}:{context.user_id}", limit=30, window_seconds=60)
    if not allowed:
        raise HTTPException(status_code=429, detail="AI request rate limit exceeded")

    if "تسجيل" in payload.prompt or "enroll" in payload.prompt.lower():
        decision = _authorization.decide(context, Permission.COURSE_ENROLL, write=True)
        return AgentResponse(
            intent="COURSE_REGISTRATION",
            action_type="WRITE",
            requires_confirmation=decision.requires_confirmation,
            confirmation_payload={
                "course_code": "SWE-432",
                "credits": 3,
                "tenant_id": tenant_id,
                "authorization": decision.reason,
            },
            response_text="تم تحليل الطلب. سيُطلب تأكيد صريح قبل تنفيذ تسجيل المقرر.",
        )

    if not settings.AI_ENABLED:
        return AgentResponse(
            intent="INFORMATION_QUERY",
            action_type="READ",
            requires_confirmation=False,
            response_text="المساعد الذكي مصرح به لهذا الطالب، لكن مزود الذكاء الاصطناعي غير مفعّل في إعدادات الجامعة.",
        )

    if not settings.DEFAULT_API_KEY:
        raise HTTPException(status_code=503, detail="AI provider is not configured")

    url = settings.AI_BASE_URL.rstrip("/") + "/chat/completions"
    headers = {
        "Authorization": f"Bearer {settings.DEFAULT_API_KEY}",
        "Content-Type": "application/json",
    }
    body_base = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a university assistant. Respect tenant scope and student permissions. "
                    "Do not claim actions were performed unless the platform confirms them."
                ),
            },
            {"role": "user", "content": payload.prompt},
        ],
    }

    last_error = "AI provider unavailable"
    async with httpx.AsyncClient(timeout=30.0) as client:
        for model in _model_candidates():
            try:
                response = await client.post(url, headers=headers, json={**body_base, "model": model})
                response.raise_for_status()
                data = response.json()
                text = data["choices"][0]["message"]["content"]
                async with SessionLocal() as session:
                    session.add(AuditLog(
                        id=str(uuid4()),
                        tenant_id=tenant_id,
                        actor_id=context.user_id,
                        action="ai.execute",
                        resource_type="ai_request",
                        status="success",
                        metadata_json="{}",
                    ))
                    await session.commit()
                return AgentResponse(
                    intent="INFORMATION_QUERY",
                    action_type="READ",
                    requires_confirmation=False,
                    response_text=text,
                )
            except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as exc:
                last_error = f"{type(exc).__name__}: provider request failed"
                continue

    async with SessionLocal() as session:
        session.add(AuditLog(
            id=str(uuid4()),
            tenant_id=tenant_id,
            actor_id=context.user_id,
            action="ai.execute",
            resource_type="ai_request",
            status="failed",
            metadata_json="{}",
        ))
        await session.commit()

    raise HTTPException(status_code=502, detail=last_error)
