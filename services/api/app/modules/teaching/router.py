from __future__ import annotations

from typing import List

from fastapi import APIRouter, Request
from pydantic import BaseModel

from app.core.access_control import AccessPolicy, Permission, request_access_context

router = APIRouter()
_policy = AccessPolicy()


class StudentGroup(BaseModel):
    id: str
    course_id: str
    name: str
    student_ids: List[str]


class AttendanceEntry(BaseModel):
    student_id: str
    present: bool


class CoursePublication(BaseModel):
    course_id: str
    title: str
    content: str
    published: bool = True


@router.post("/groups", response_model=StudentGroup)
async def create_group(request: Request, course_id: str, name: str) -> StudentGroup:
    context = request_access_context(request)
    _policy.require(context, Permission.CREATE_GROUP)
    return StudentGroup(id="grp_pending", course_id=course_id, name=name, student_ids=[])


@router.post("/attendance", response_model=List[AttendanceEntry])
async def record_attendance(request: Request, entries: List[AttendanceEntry]) -> List[AttendanceEntry]:
    context = request_access_context(request)
    _policy.require(context, Permission.ATTENDANCE_WRITE)
    return entries


@router.post("/courses/publish", response_model=CoursePublication)
async def publish_course(request: Request, payload: CoursePublication) -> CoursePublication:
    context = request_access_context(request)
    _policy.require(context, Permission.PUBLISH_COURSE)
    return payload
