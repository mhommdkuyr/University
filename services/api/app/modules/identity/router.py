from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import StudentStatus, request_access_context
from app.core.database import User, get_session
from app.integrations.frappe_education import FrappeEducationClient


router = APIRouter()


class IdentityLookup(BaseModel):
    university_student_number: str
    source_system: str = "university"


class IdentityResult(BaseModel):
    found: bool
    tenant_id: str
    student_number: str
    status: StudentStatus | None = None
    identity_state: Literal["unverified", "verified", "revoked"] = "unverified"
    message: str


@router.post("/verify", response_model=IdentityResult)
async def verify_university_identity(
    request: Request,
    payload: IdentityLookup,
    session: AsyncSession = Depends(get_session),
) -> IdentityResult:
    tenant_id = getattr(request.state, "tenant_id", "default")

    if payload.source_system.lower() in {"frappe", "frappe_education", "erpnext"}:
        client = FrappeEducationClient()
        if not client.config.enabled:
            raise HTTPException(status_code=503, detail="Frappe Education connector is not configured")
        try:
            student = await client.find_student_by_number(payload.university_student_number)
        except Exception as exc:
            raise HTTPException(status_code=502, detail="External university identity source is unavailable") from exc
        if not student:
            return IdentityResult(
                found=False,
                tenant_id=tenant_id,
                student_number=payload.university_student_number,
                message="No matching student record was found in Frappe Education.",
            )
        enabled = bool(student.get("enabled", True))
        return IdentityResult(
            found=True,
            tenant_id=tenant_id,
            student_number=payload.university_student_number,
            status=StudentStatus.ACTIVE if enabled else StudentStatus.INACTIVE,
            identity_state="verified" if enabled else "revoked",
            message="Identity verified against the configured Frappe Education source.",
        )

    user = await session.scalar(
        select(User).where(
            User.tenant_id == tenant_id,
            User.student_number == payload.university_student_number,
        )
    )
    if user is None:
        return IdentityResult(
            found=False,
            tenant_id=tenant_id,
            student_number=payload.university_student_number,
            message="No matching student record was found in the configured identity source.",
        )

    try:
        state = StudentStatus(user.student_status) if user.student_status else None
    except ValueError:
        state = None

    return IdentityResult(
        found=True,
        tenant_id=tenant_id,
        student_number=payload.university_student_number,
        status=state,
        identity_state="verified" if user.is_active else "revoked",
        message="Identity matched the platform's configured university source.",
    )


@router.get("/me")
async def current_identity(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    user = await session.scalar(
        select(User).where(User.id == context.user_id, User.tenant_id == context.tenant_id)
    )
    if user is None:
        return {"authenticated": False}

    return {
        "authenticated": True,
        "user_id": user.id,
        "tenant_id": user.tenant_id,
        "full_name": user.full_name,
        "email": user.email,
        "student_number": user.student_number,
        "role": user.role,
        "student_status": user.student_status,
    }
