from app.core.access_control import (
    AccessPolicy,
    Permission,
    PlatformRole,
    StudentStatus,
)
from app.modules.access.service import AuthorizationService


def test_active_student_gets_ai_access():
    policy = AccessPolicy()
    context = policy.build_context(
        tenant_id="11111111-1111-1111-1111-111111111111",
        user_id="student-1",
        role=PlatformRole.STUDENT,
        student_status=StudentStatus.ACTIVE,
    )
    assert Permission.USE_AI in context.permissions
    assert context.is_active_student


def test_graduate_loses_academic_and_ai_access():
    policy = AccessPolicy()
    context = policy.build_context(
        tenant_id="11111111-1111-1111-1111-111111111111",
        user_id="student-2",
        role=PlatformRole.STUDENT,
        student_status=StudentStatus.GRADUATED,
    )
    assert Permission.USE_AI not in context.permissions
    assert Permission.VIEW_ACADEMICS not in context.permissions


def test_instructor_can_manage_attendance_and_groups():
    policy = AccessPolicy()
    context = policy.build_context(
        tenant_id="11111111-1111-1111-1111-111111111111",
        user_id="teacher-1",
        role=PlatformRole.INSTRUCTOR,
    )
    assert Permission.CREATE_GROUP in context.permissions
    assert Permission.ATTENDANCE_WRITE in context.permissions
    assert Permission.PUBLISH_COURSE in context.permissions


def test_instructor_sensitive_write_requires_confirmation():
    policy = AccessPolicy()
    context = policy.build_context(
        tenant_id="11111111-1111-1111-1111-111111111111",
        user_id="teacher-1",
        role=PlatformRole.INSTRUCTOR,
    )
    decision = AuthorizationService().decide(context, Permission.ATTENDANCE_WRITE, write=True)
    assert decision.allowed
    assert decision.requires_confirmation
