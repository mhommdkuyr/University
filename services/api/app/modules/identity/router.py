from __future__ import annotations

from typing import Literal, Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.access_control import StudentStatus

router = APIRouter()


class IdentityLookup(BaseModel):
    university_student_number: str
    source_system: str = "university"


class IdentityResult(BaseModel):
    found: bool
    tenant_id: str
    student_number: str
    status: Optional[StudentStatus] = None
    identity_state: Literal["unverified", "verified", "revoked"] = "unverified"
    message: str


@router.post("/verify", response_model=IdentityResult)
async def verify_university_identity(request: Request, payload: IdentityLookup) -> IdentityResult:
    """Integration boundary for university identity systems.

    The production adapter will query the university's authoritative source and
    return the current enrollment state. No password is derived from a student ID.
    """
    tenant_id = getattr(request.state, "tenant_id", "default")
    return IdentityResult(
        found=False,
        tenant_id=tenant_id,
        student_number=payload.university_student_number,
        message="Connect the university identity adapter to perform authoritative verification.",
    )
