from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import Permission, request_access_context
from app.core.database import AuditLog, Project, get_session


router = APIRouter()


class ProjectResponse(BaseModel):
    id: str
    title: str
    slug: str
    department: str
    status: str
    description: str
    public_url: str


class ProjectCreate(BaseModel):
    title: str = Field(min_length=2, max_length=255)
    slug: str = Field(min_length=2, max_length=160)
    department: str = ""
    description: str = ""
    publish: bool = False


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(
    request: Request,
    department: str | None = None,
    session: AsyncSession = Depends(get_session),
):
    tenant_id = request.headers.get("X-Tenant-ID") or getattr(request.state, "tenant_id", "default")
    query = select(Project).where(Project.tenant_id == tenant_id, Project.status == "approved")
    if department:
        query = query.where(Project.department == department)
    rows = (await session.scalars(query.order_by(Project.created_at.desc()))).all()
    return [ProjectResponse.model_validate(row, from_attributes=True) for row in rows]


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    payload: ProjectCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if Permission.PROJECT_MANAGE not in context.permissions:
        raise HTTPException(status_code=403, detail="Project management denied")

    existing = await session.scalar(
        select(Project).where(Project.tenant_id == context.tenant_id, Project.slug == payload.slug)
    )
    if existing:
        raise HTTPException(status_code=409, detail="Project slug already exists")

    project = Project(
        id=str(uuid4()),
        tenant_id=context.tenant_id,
        owner_id=context.user_id,
        title=payload.title,
        slug=payload.slug,
        department=payload.department,
        status="approved" if payload.publish else "draft",
        description=payload.description,
        public_url=f"/projects/{payload.slug}",
    )
    session.add(project)
    session.add(AuditLog(
        id=str(uuid4()),
        tenant_id=context.tenant_id,
        actor_id=context.user_id,
        action="project.create",
        resource_type="project",
        status="success",
        metadata_json="{}",
    ))
    await session.commit()
    await session.refresh(project)
    return ProjectResponse.model_validate(project, from_attributes=True)
