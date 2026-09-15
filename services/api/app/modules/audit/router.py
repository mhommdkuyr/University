from fastapi import APIRouter, Request
from pydantic import BaseModel
from typing import List

router = APIRouter()

class AuditEntry(BaseModel):
    id: str
    action: str
    resource_type: str
    status: str
    timestamp: str

@router.get("/logs", response_model=List[AuditEntry])
async def get_audit_logs(request: Request):
    return [
        {
            "id": "aud_01",
            "action": "project.approve",
            "resource_type": "project",
            "status": "success",
            "timestamp": "2026-09-15T12:00:00Z"
        }
    ]
