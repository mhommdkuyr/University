from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()

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
    tenant_id = getattr(request.state, "tenant_id", "default")
    # Simulation of Agent Permission Flow
    if "تسجيل" in payload.prompt or "enroll" in payload.prompt.lower():
        return {
            "intent": "COURSE_REGISTRATION",
            "action_type": "WRITE",
            "requires_confirmation": True,
            "confirmation_payload": {
                "course_code": "SWE-432",
                "credits": 3,
                "tenant_id": tenant_id
            },
            "response_text": "تم فحص المتطلبات المسبقة والجدول. يرجى تأكيد تسجيل مقرر SWE-432."
        }
    return {
        "intent": "INFORMATION_QUERY",
        "action_type": "READ",
        "requires_confirmation": False,
        "response_text": f"مرحباً بك في مساعد جامعة {tenant_id}. كيف يمكنني خدمتك اليوم؟"
    }
