from __future__ import annotations

from typing import Dict, List

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from app.core.access_control import Permission, PlatformRole, ROLE_DEFAULT_PERMISSIONS

router = APIRouter()


class RolePolicy(BaseModel):
    role: PlatformRole
    permissions: List[Permission]


class RolePolicyUpdate(BaseModel):
    permissions: List[Permission] = Field(default_factory=list)


@router.get("/catalog", response_model=List[RolePolicy])
async def role_catalog() -> List[RolePolicy]:
    return [
        RolePolicy(role=role, permissions=sorted(perms, key=lambda item: item.value))
        for role, perms in ROLE_DEFAULT_PERMISSIONS.items()
    ]


@router.get("/policies", response_model=Dict[str, List[str]])
async def get_tenant_role_policies(request: Request) -> Dict[str, List[str]]:
    """Return effective defaults for the current university.

    Tenant overrides are persisted in tenant_role_policies. The repository layer
    can later overlay those rows without changing this API contract.
    """
    _tenant_id = getattr(request.state, "tenant_id", "default")
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
    """Validate a tenant policy payload.

    A production persistence adapter must require MANAGE_ROLE_POLICY before write
    and execute the mutation inside the tenant RLS transaction.
    """
    _tenant_id = getattr(request.state, "tenant_id", "default")
    return RolePolicy(role=role, permissions=payload.permissions)
