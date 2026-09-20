from __future__ import annotations

import hashlib
import json

from fastapi import Request
from jose import JWTError
from sqlalchemy import select
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.access_control import AccessContext, AccessPolicy, Permission, PlatformRole, StudentStatus
from app.core.database import ApiClientKey, RolePolicyRecord, SessionLocal
from app.core.security import decode_access_token


class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        header_tenant = request.headers.get("X-Tenant-ID")
        request.state.tenant_id = header_tenant or "default"

        path = request.url.path
        public_request = (
            path in {"/api/v1/health", "/api/v1/docs", "/api/v1/openapi.json", "/api/v1/auth/login"}
            or (request.method == "GET" and path.startswith("/api/v1/projects"))
            or (request.method == "GET" and path == "/api/v1/search/semantic")
        )
        if public_request:
            return await call_next(request)

        authorization = request.headers.get("Authorization", "")
        api_key = request.headers.get("X-API-Key", "")

        if not authorization.startswith("Bearer ") and api_key:
            key_hash = hashlib.sha256(api_key.encode("utf-8")).hexdigest()
            async with SessionLocal() as session:
                record = await session.scalar(
                    select(ApiClientKey).where(
                        ApiClientKey.key_hash == key_hash,
                        ApiClientKey.active.is_(True),
                    )
                )
                if record is not None:
                    if header_tenant and header_tenant != record.tenant_id:
                        request.state.auth_error = "Tenant mismatch"
                        return await call_next(request)
                    try:
                        scoped_permissions = {Permission(item) for item in json.loads(record.scopes)}
                    except (ValueError, TypeError, json.JSONDecodeError):
                        request.state.auth_error = "Invalid API key scopes"
                        return await call_next(request)
                    permissions = frozenset(scoped_permissions | {
                        Permission.VIEW_PUBLIC,
                        Permission.VIEW_PUBLIC_PROJECTS,
                    })
                    request.state.tenant_id = record.tenant_id
                    request.state.access_context = AccessContext(
                        tenant_id=record.tenant_id,
                        user_id=record.created_by,
                        role=PlatformRole.DEVELOPER,
                        student_status=None,
                        permissions=permissions,
                    )
                    return await call_next(request)

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
