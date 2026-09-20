from __future__ import annotations

import hashlib
import json
import secrets
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import Permission, request_access_context
from app.core.database import ApiClientKey, AuditLog, get_session


router = APIRouter()

SAFE_API_SCOPES = {
    Permission.VIEW_PUBLIC,
    Permission.VIEW_PUBLIC_PROJECTS,
    Permission.VIEW_ACADEMICS,
}


class ApiKeyCreate(BaseModel):
    name: str = Field(min_length=2, max_length=255)
    scopes: list[Permission] = Field(default_factory=lambda: [
        Permission.VIEW_PUBLIC,
        Permission.VIEW_PUBLIC_PROJECTS,
    ])


class ApiKeyCreated(BaseModel):
    id: str
    name: str
    prefix: str
    scopes: list[Permission]
    api_key: str
    created_at: str


class ApiKeyView(BaseModel):
    id: str
    name: str
    prefix: str
    scopes: list[Permission]
    active: bool
    created_at: str
    revoked_at: str | None = None


def _hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@router.post("/keys", response_model=ApiKeyCreated, status_code=201)
async def create_api_key(
    payload: ApiKeyCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if Permission.MANAGE_API_KEYS not in context.permissions:
        raise HTTPException(status_code=403, detail="API key management denied")

    requested = set(payload.scopes)
    if not requested.issubset(SAFE_API_SCOPES):
        raise HTTPException(status_code=400, detail="Requested API scope is not available")

    raw = "univ_live_" + secrets.token_urlsafe(32)
    prefix = raw[:18]
    now = datetime.now(timezone.utc)
    record = ApiClientKey(
        id=str(uuid4()),
        tenant_id=context.tenant_id,
        name=payload.name,
        prefix=prefix,
        key_hash=_hash(raw),
        scopes=json.dumps(sorted(item.value for item in requested)),
        created_by=context.user_id,
        active=True,
        created_at=now,
    )
    session.add(record)
    session.add(AuditLog(
        id=str(uuid4()),
        tenant_id=context.tenant_id,
        actor_id=context.user_id,
        action="api_key.create",
        resource_type="api_key",
        status="success",
        metadata_json=json.dumps({"key_prefix": prefix}),
    ))
    await session.commit()

    return ApiKeyCreated(
        id=record.id,
        name=record.name,
        prefix=record.prefix,
        scopes=sorted(requested, key=lambda item: item.value),
        api_key=raw,
        created_at=now.isoformat(),
    )


@router.get("/keys", response_model=list[ApiKeyView])
async def list_api_keys(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if Permission.MANAGE_API_KEYS not in context.permissions:
        raise HTTPException(status_code=403, detail="API key management denied")

    rows = (
        await session.scalars(
            select(ApiClientKey)
            .where(ApiClientKey.tenant_id == context.tenant_id)
            .order_by(ApiClientKey.created_at.desc())
        )
    ).all()

    return [
        ApiKeyView(
            id=row.id,
            name=row.name,
            prefix=row.prefix,
            scopes=[Permission(item) for item in json.loads(row.scopes)],
            active=row.active,
            created_at=row.created_at.isoformat(),
            revoked_at=row.revoked_at.isoformat() if row.revoked_at else None,
        )
        for row in rows
    ]


@router.post("/keys/{key_id}/revoke", response_model=ApiKeyView)
async def revoke_api_key(
    key_id: str,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if Permission.MANAGE_API_KEYS not in context.permissions:
        raise HTTPException(status_code=403, detail="API key management denied")

    row = await session.scalar(
        select(ApiClientKey).where(
            ApiClientKey.id == key_id,
            ApiClientKey.tenant_id == context.tenant_id,
        )
    )
    if row is None:
        raise HTTPException(status_code=404, detail="API key not found")

    row.active = False
    row.revoked_at = datetime.now(timezone.utc)
    session.add(AuditLog(
        id=str(uuid4()),
        tenant_id=context.tenant_id,
        actor_id=context.user_id,
        action="api_key.revoke",
        resource_type="api_key",
        status="success",
        metadata_json=json.dumps({"key_prefix": row.prefix}),
    ))
    await session.commit()

    return ApiKeyView(
        id=row.id,
        name=row.name,
        prefix=row.prefix,
        scopes=[Permission(item) for item in json.loads(row.scopes)],
        active=row.active,
        created_at=row.created_at.isoformat(),
        revoked_at=row.revoked_at.isoformat() if row.revoked_at else None,
    )
