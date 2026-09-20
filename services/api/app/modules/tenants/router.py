from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import Permission, PlatformRole, request_access_context
from app.core.database import Tenant, get_session


router = APIRouter()


class TenantItem(BaseModel):
    id: str
    slug: str
    name: str
    plan: str
    status: str


class TenantCreate(BaseModel):
    slug: str = Field(min_length=2, max_length=100, pattern=r"^[a-z0-9-]+$")
    name: str = Field(min_length=2, max_length=255)
    plan: str = "starter"


@router.get("/", response_model=list[TenantItem])
async def list_tenants(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if context.role != PlatformRole.PLATFORM_ADMIN:
        raise HTTPException(status_code=403, detail="Platform administration required")

    rows = (await session.scalars(select(Tenant).order_by(Tenant.name))).all()
    return [
        TenantItem(id=row.id, slug=row.slug, name=row.name, plan=row.plan, status=row.status)
        for row in rows
    ]


@router.post("/", response_model=TenantItem, status_code=201)
async def create_tenant(
    payload: TenantCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if context.role != PlatformRole.PLATFORM_ADMIN or Permission.MANAGE_UNIVERSITY not in context.permissions:
        raise HTTPException(status_code=403, detail="Platform administration required")

    existing = await session.scalar(select(Tenant).where(Tenant.slug == payload.slug))
    if existing:
        raise HTTPException(status_code=409, detail="Tenant slug already exists")

    tenant = Tenant(
        id=str(uuid4()),
        slug=payload.slug,
        name=payload.name,
        plan=payload.plan,
        status="active",
    )
    session.add(tenant)
    await session.commit()
    return TenantItem(
        id=tenant.id,
        slug=tenant.slug,
        name=tenant.name,
        plan=tenant.plan,
        status=tenant.status,
    )
