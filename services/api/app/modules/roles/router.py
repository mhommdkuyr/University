from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.access_control import Permission, PlatformRole, ROLE_DEFAULT_PERMISSIONS, request_access_context

router = APIRouter()


class RolePolicy(BaseModel):
    role: PlatformRole
    permissions: List[Permission]


class RolePolicyUpdate(BaseModel):
    permissions: List[Permission] = Field(default_factory=list)


@router.get("/catalog", response_model=List[RolePolicy])
async def role_catalog(request: Request) -> List[RolePolicy]:
    # The catalog itself is descriptive and contains no tenant-private records.
    _ = request
    return [
        RolePolicy(role=role, permissions=sorted(perms, key=lambda item: item.value))
        for role, perms in ROLE_DEFAULT_PERMISSIONS.items()
    ]


@router.get("/policies", response_model=Dict[str, List[str]])
async def get_tenant_role_policies(request: Request) -> Dict[str, List[str]]:
    context = request_access_context(request)
    if Permission.MANAGE_ROLE_POLICY not in context.permissions:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Role policy access denied")
    return {
        role.value: [permission.value for permission in permissions]
        for role, permissions in ROLE_DEFAULT_PERMISSIONS.items()
    }


@router.put("/policies/{role}", response_model=RolePolicy)
async def set_tenant_role_policy(
    role: PlatformRole,
    payload: RolePolicyUpdate,
    request: Request,
) -> RolePolicy:
    context = request_access_context(request)
    if Permission.MANAGE_ROLE_POLICY not in context.permissions:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Role policy modification denied")
    return RolePolicy(role=role, permissions=payload.permissions)
