from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AuditLog, Tenant, User, get_session
from app.core.rate_limit import limiter
from app.core.security import create_access_token, verify_password


router = APIRouter()


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    tenant_id: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    tenant_id: str
    user_id: str
    role: str
    full_name: str
    expires_in: int


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    request: Request,
    session: AsyncSession = Depends(get_session),
    x_tenant_id: str | None = Header(default=None),
):
    client_key = request.client.host if request.client else "unknown"
    email_key = str(payload.email).lower()
    allowed = await limiter.allow(f"login:{client_key}:{email_key}", limit=8, window_seconds=300)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
        )

    tenant_id = payload.tenant_id or x_tenant_id

    if tenant_id:
        user = await session.scalar(
            select(User).where(User.tenant_id == tenant_id, User.email == email_key)
        )
    else:
        matches = (await session.scalars(select(User).where(User.email == email_key))).all()
        if len(matches) != 1:
            raise HTTPException(
                status_code=400,
                detail="tenant_id is required when the account exists in multiple universities",
            )
        user = matches[0]
        tenant_id = user.tenant_id

    if user is None or not user.is_active or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    tenant = await session.scalar(select(Tenant).where(Tenant.id == tenant_id))
    if tenant is None or tenant.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="University account is not active")

    token = create_access_token({
        "sub": user.id,
        "tenant_id": tenant.id,
        "role": user.role,
        "student_status": user.student_status,
    })

    session.add(AuditLog(
        id=str(uuid4()),
        tenant_id=tenant.id,
        actor_id=user.id,
        action="auth.login",
        resource_type="session",
        status="success",
        metadata_json="{}",
    ))
    await session.commit()

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        tenant_id=tenant.id,
        user_id=user.id,
        role=user.role,
        full_name=user.full_name,
        expires_in=60 * settings_expiry_minutes(),
    )


def settings_expiry_minutes() -> int:
    from app.core.config import settings
    return settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
