from __future__ import annotations

import json
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import Permission, request_access_context
from app.core.database import AttendanceRecord, Course, StudentGroup as StudentGroupModel, get_session


router = APIRouter()


class StudentGroupCreate(BaseModel):
    course_id: str
    name: str = Field(min_length=2, max_length=255)
    student_ids: list[str] = Field(default_factory=list)


class StudentGroup(BaseModel):
    id: str
    course_id: str
    name: str
    student_ids: list[str]


class AttendanceEntry(BaseModel):
    student_id: str
    course_id: str
    present: bool


class CoursePublication(BaseModel):
    course_id: str
    code: str
    title: str
    credits: int = Field(ge=1, le=30)
    content: str = ""
    published: bool = True


@router.post("/groups", response_model=StudentGroup, status_code=201)
async def create_group(
    payload: StudentGroupCreate,
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if Permission.CREATE_GROUP not in context.permissions:
        raise HTTPException(status_code=403, detail="Group creation denied")

    group = StudentGroupModel(
        id=str(uuid4()),
        tenant_id=context.tenant_id,
        course_id=payload.course_id,
        name=payload.name,
        student_ids=json.dumps(payload.student_ids),
    )
    session.add(group)
    await session.commit()
    return StudentGroup(
        id=group.id,
        course_id=group.course_id,
        name=group.name,
        student_ids=payload.student_ids,
    )


@router.post("/attendance", response_model=list[AttendanceEntry])
async def record_attendance(
    request: Request,
    entries: list[AttendanceEntry],
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if Permission.ATTENDANCE_WRITE not in context.permissions:
        raise HTTPException(status_code=403, detail="Attendance write denied")

    for entry in entries:
        existing = await session.scalar(
            select(AttendanceRecord).where(
                AttendanceRecord.tenant_id == context.tenant_id,
                AttendanceRecord.student_id == entry.student_id,
                AttendanceRecord.course_id == entry.course_id,
            )
        )
        if existing is None:
            session.add(AttendanceRecord(
                id=str(uuid4()),
                tenant_id=context.tenant_id,
                student_id=entry.student_id,
                course_id=entry.course_id,
                present=entry.present,
                recorded_by=context.user_id,
            ))
        else:
            existing.present = entry.present
            existing.recorded_by = context.user_id

    await session.commit()
    return entries


@router.post("/courses/publish", response_model=CoursePublication)
async def publish_course(
    request: Request,
    payload: CoursePublication,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    if Permission.PUBLISH_COURSE not in context.permissions:
        raise HTTPException(status_code=403, detail="Course publishing denied")

    course = await session.scalar(
        select(Course).where(
            Course.tenant_id == context.tenant_id,
            Course.id == payload.course_id,
        )
    )
    if course is None:
        course = Course(
            id=payload.course_id,
            tenant_id=context.tenant_id,
            code=payload.code,
            title=payload.title,
            credits=payload.credits,
            content=payload.content,
            published=payload.published,
        )
        session.add(course)
    else:
        course.code = payload.code
        course.title = payload.title
        course.credits = payload.credits
        course.content = payload.content
        course.published = payload.published

    await session.commit()
    return payload
