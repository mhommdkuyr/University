from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import Permission, PlatformRole, request_access_context
from app.core.database import Course, get_session


router = APIRouter()


class CourseSchema(BaseModel):
    id: str
    code: str
    title: str
    credits: int
    published: bool


@router.get("/courses", response_model=list[CourseSchema])
async def list_courses(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = getattr(request.state, "access_context", None)
    if context is None:
        raise HTTPException(status_code=401, detail="Authentication required")
    tenant_id = context.tenant_id
    query = select(Course).where(Course.tenant_id == tenant_id)
    if context.role == PlatformRole.DEVELOPER:
        query = query.where(Course.published.is_(True))
    elif Permission.VIEW_ACADEMICS not in context.permissions:
        query = query.where(Course.published.is_(True))
    rows = (await session.scalars(query.order_by(Course.code))).all()
    return [CourseSchema.model_validate(row, from_attributes=True) for row in rows]
