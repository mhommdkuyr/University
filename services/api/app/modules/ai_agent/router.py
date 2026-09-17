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
    discipline: str = "computer_science"  # computer_science, engineering, arts_design, business, medicine, humanities
    department_id: Optional[str] = None


class AgentResponse(BaseModel):
    intent: str
    discipline: str
    action_type: str
    requires_confirmation: bool
    confirmation_payload: Optional[Dict[str, Any]] = None
    response_text: str
    suggested_tools: list[str]


DISCIPLINE_TOOLS = {
    "computer_science": ["code_executor", "database_query_builder", "api_tester"],
    "engineering": ["cad_viewer", "structural_calculator", "simulation_engine"],
    "arts_design": ["palette_generator", "portfolio_analyzer", "image_upscaler"],
    "business": ["market_analyst", "financial_modeler", "chart_builder"],
    "medicine": ["literature_search", "anatomy_viewer", "case_summarizer"],
    "humanities": ["citation_generator", "text_summarizer", "source_verifier"],
}


@router.post("/execute", response_model=AgentResponse)
async def execute_agent_command(request: Request, payload: AgentRequest):
    context = request_access_context(request)
    _access.require_active_student(context)
    _access.require(context, Permission.USE_AI)

    tenant_id = context.tenant_id
    discipline = payload.discipline if payload.discipline in DISCIPLINE_TOOLS else "computer_science"
    tools = DISCIPLINE_TOOLS.get(discipline, [])

    # The model may propose an intent, but deterministic authorization decides access.
    if "تسجيل" in payload.prompt or "enroll" in payload.prompt.lower():
        decision = _authorization.decide(context, Permission.COURSE_ENROLL, write=True)
        return AgentResponse(
            intent="COURSE_REGISTRATION",
            discipline=discipline,
            action_type="WRITE",
            requires_confirmation=decision.requires_confirmation,
            confirmation_payload={
                "course_code": "SWE-432",
                "credits": 3,
                "tenant_id": tenant_id,
                "authorization": decision.reason,
            },
            response_text="تم تحليل الطلب. سيُطلب تأكيد صريح قبل تنفيذ تسجيل المقرر.",
            suggested_tools=tools,
        )

    return AgentResponse(
        intent="SPECIALIZED_DISCIPLINE_QUERY",
        discipline=discipline,
        action_type="READ",
        requires_confirmation=False,
        response_text=f"مركز الذكاء الاصطناعي المتخصص ({discipline}) للجامعة {tenant_id}.",
        suggested_tools=tools,
    )
