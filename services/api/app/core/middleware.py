from __future__ import annotations

import json

from fastapi import Request
from jose import JWTError
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.access_control import AccessContext, AccessPolicy, Permission, PlatformRole, StudentStatus
from app.core.database import RolePolicyRecord, SessionLocal
from app.core.security import decode_access_token


PUBLIC_PREFIXES = (
    "/api/v1/health",
    "/api/v1/docs",
    "/api/v1/openapi.json",
    "/api/v1/auth/login",
    "/api/v1/projects",
    "/api/v1/search/semantic",
)


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        header_tenant = request.headers.get("X-Tenant-ID")
        request.state.tenant_id = header_tenant or "default"

        if request.url.path.startswith(PUBLIC_PREFIXES):
            return await call_next(request)

        authorization = request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            return await call_next(request)

        token = authorization[7:].strip()
        try:
            claims = decode_access_token(token)
            tenant_id = str(claims["tenant_id"])
            user_id = str(claims["sub"])
            role = PlatformRole(str(claims["role"]))
            raw_status = claims.get("student_status")
            student_status = StudentStatus(str(raw_status)) if raw_status else None
        except (ValueError, KeyError, JWTError):
            request.state.auth_error = "Invalid access token"
            return await call_next(request)

        if header_tenant and header_tenant != tenant_id:
            request.state.auth_error = "Tenant mismatch"
            return await call_next(request)

        permissions = set(AccessPolicy().permissions_for(tenant_id, role))
        async with SessionLocal() as session:
            record = await session.scalar(
                select(RolePolicyRecord).where(
                    RolePolicyRecord.tenant_id == tenant_id,
                    RolePolicyRecord.role == role.value,
                )
            )
            if record is not None:
                try:
                    permissions = {Permission(item) for item in json.loads(record.permissions)}
                except (ValueError, TypeError, json.JSONDecodeError):
                    permissions = set()

        if role == PlatformRole.STUDENT and student_status != StudentStatus.ACTIVE:
            permissions.discard(Permission.USE_AI)
            permissions.discard(Permission.VIEW_ACADEMICS)
            permissions.discard(Permission.COURSE_ENROLL)

        request.state.tenant_id = tenant_id
        request.state.access_context = AccessContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            student_status=student_status,
            permissions=frozenset(permissions),
        )

        return await call_next(request)
