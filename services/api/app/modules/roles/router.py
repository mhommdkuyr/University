from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import Permission, PlatformRole, ROLE_DEFAULT_PERMISSIONS, request_access_context
from app.core.database import RolePolicyRecord, get_session


router = APIRouter()


class RolePolicy(BaseModel):
    role: PlatformRole
    permissions: list[Permission]


class RolePolicyUpdate(BaseModel):
    permissions: list[Permission] = Field(default_factory=list)


@router.get("/catalog", response_model=list[RolePolicy])
async def role_catalog() -> list[RolePolicy]:
    return [
        RolePolicy(role=role, permissions=sorted(perms, key=lambda item: item.value))
        for role, perms in ROLE_DEFAULT_PERMISSIONS.items()
    ]


@router.get("/policies", response_model=dict[str, list[str]])
async def get_tenant_role_policies(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if Permission.MANAGE_ROLE_POLICY not in context.permissions:
        raise HTTPException(status_code=403, detail="Role policy access denied")

    result: dict[str, list[str]] = {}
    for role, permissions in ROLE_DEFAULT_PERMISSIONS.items():
        record = await session.scalar(
            select(RolePolicyRecord).where(
                RolePolicyRecord.tenant_id == context.tenant_id,
                RolePolicyRecord.role == role.value,
            )
        )
        if record is None:
            result[role.value] = [item.value for item in permissions]
        else:
            result[role.value] = json.loads(record.permissions)
    return result


@router.put("/policies/{role}", response_model=RolePolicy)
async def set_tenant_role_policy(
    role: PlatformRole,
    payload: RolePolicyUpdate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if Permission.MANAGE_ROLE_POLICY not in context.permissions:
        raise HTTPException(status_code=403, detail="Role policy modification denied")
    if role in {PlatformRole.PLATFORM_ADMIN, PlatformRole.UNIVERSITY_PRESIDENT}:
        raise HTTPException(status_code=403, detail="Protected platform roles cannot be modified by this endpoint")

    record = await session.scalar(
        select(RolePolicyRecord).where(
            RolePolicyRecord.tenant_id == context.tenant_id,
            RolePolicyRecord.role == role.value,
        )
    )
    encoded = json.dumps([permission.value for permission in payload.permissions])
    if record is None:
        session.add(RolePolicyRecord(
            id=str(uuid4()),
            tenant_id=context.tenant_id,
            role=role.value,
            permissions=encoded,
        ))
    else:
        record.permissions = encoded

    await session.commit()
    return RolePolicy(role=role, permissions=payload.permissions)
