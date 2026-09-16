from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.access_control import AccessPolicy, Permission, request_access_context
from app.modules.access.service import AuthorizationService

router = APIRouter()
_access = AccessPolicy()
_authorization = AuthorizationService()


class AgentRequest(BaseModel):
    prompt: str
    user_role: str = "student"


class AgentResponse(BaseModel):
    intent: str
    action_type: str
    requires_confirmation: bool
    confirmation_payload: Optional[Dict[str, Any]] = None
    response_text: str


@router.post("/execute", response_model=AgentResponse)
async def execute_agent_command(request: Request, payload: AgentRequest):
    context = request_access_context(request)
    _access.require_active_student(context)
    _access.require(context, Permission.USE_AI)

    tenant_id = context.tenant_id
    # The model may propose an intent, but deterministic authorization decides access.
    if "تسجيل" in payload.prompt or "enroll" in payload.prompt.lower():
        decision = _authorization.decide(context, Permission.VIEW_ACADEMICS, write=True)
        return {
            "intent": "COURSE_REGISTRATION",
            "action_type": "WRITE",
            "requires_confirmation": True,
            "confirmation_payload": {
                "course_code": "SWE-432",
                "credits": 3,
                "tenant_id": tenant_id,
                "authorization": decision.reason,
            },
            "response_text": "تم تحليل الطلب. سيُطلب تأكيد صريح قبل تنفيذ تسجيل المقرر.",
        }

    return {
        "intent": "INFORMATION_QUERY",
        "action_type": "READ",
        "requires_confirmation": False,
        "response_text": f"مساعد الجامعة للطالب النشط: {tenant_id}",
    }
