"""Tenant-aware authorization primitives for the University platform.

The model is intentionally deterministic: the AI layer may propose an action,
but only this service can decide whether that action is allowed.
"""
from dataclasses import dataclass
from enum import Enum
from typing import Iterable, Mapping

from fastapi import HTTPException, Request, status


class StudentStatus(str, Enum):
    ACTIVE = "active"
    GRADUATED = "graduated"
    SUSPENDED = "suspended"
    WITHDRAWN = "withdrawn"
    EXPELLED = "expelled"
    INACTIVE = "inactive"


class PlatformRole(str, Enum):
    PLATFORM_ADMIN = "platform_admin"
    UNIVERSITY_PRESIDENT = "university_president"
    UNIVERSITY_ADMIN = "university_admin"
    DEAN = "dean"
    DEPARTMENT_HEAD = "department_head"
    INSTRUCTOR = "instructor"
    REPRESENTATIVE = "representative"
    STUDENT = "student"
    DEVELOPER = "developer"
    GUEST = "guest"
    ALUMNI = "alumni"


class Permission(str, Enum):
    VIEW_ACADEMICS = "academics.view"
    USE_AI = "ai.use"
    VIEW_STUDENT_PRIVATE = "students.private.view"
    MANAGE_STUDENTS = "students.manage"
    CREATE_GROUP = "groups.create"
    MANAGE_GROUP = "groups.manage"
    ATTENDANCE_VIEW = "attendance.view"
    ATTENDANCE_WRITE = "attendance.write"
    PUBLISH_COURSE = "courses.publish"
    MANAGE_SCHEDULE = "schedule.manage"
    MANAGE_CONTENT = "content.manage"
    MANAGE_UNIVERSITY = "university.manage"
    MANAGE_ROLE_POLICY = "roles.policy.manage"
    VIEW_PUBLIC = "public.view"
    VIEW_PUBLIC_PROJECTS = "projects.public.view"
    PROJECT_MANAGE = "projects.manage"


@dataclass(frozen=True)
class AccessContext:
    tenant_id: str
    user_id: str
    role: PlatformRole
    student_status: StudentStatus | None
    permissions: frozenset[Permission]

    @property
    def is_active_student(self) -> bool:
        return self.role == PlatformRole.STUDENT and self.student_status == StudentStatus.ACTIVE


ROLE_DEFAULT_PERMISSIONS: Mapping[PlatformRole, frozenset[Permission]] = {
    PlatformRole.PLATFORM_ADMIN: frozenset(Permission),
    PlatformRole.UNIVERSITY_PRESIDENT: frozenset({
        Permission.VIEW_ACADEMICS,
        Permission.VIEW_STUDENT_PRIVATE,
        Permission.MANAGE_STUDENTS,
        Permission.MANAGE_GROUP,
        Permission.ATTENDANCE_VIEW,
        Permission.ATTENDANCE_WRITE,
        Permission.PUBLISH_COURSE,
        Permission.MANAGE_SCHEDULE,
        Permission.MANAGE_CONTENT,
        Permission.MANAGE_UNIVERSITY,
        Permission.MANAGE_ROLE_POLICY,
        Permission.VIEW_PUBLIC,
        Permission.VIEW_PUBLIC_PROJECTS,
        Permission.PROJECT_MANAGE,
    }),
    PlatformRole.UNIVERSITY_ADMIN: frozenset({
        Permission.VIEW_ACADEMICS,
        Permission.VIEW_STUDENT_PRIVATE,
        Permission.MANAGE_STUDENTS,
        Permission.MANAGE_GROUP,
        Permission.ATTENDANCE_VIEW,
        Permission.ATTENDANCE_WRITE,
        Permission.PUBLISH_COURSE,
        Permission.MANAGE_SCHEDULE,
        Permission.MANAGE_CONTENT,
        Permission.VIEW_PUBLIC,
        Permission.VIEW_PUBLIC_PROJECTS,
    }),
    PlatformRole.DEAN: frozenset({
        Permission.VIEW_ACADEMICS,
        Permission.VIEW_STUDENT_PRIVATE,
        Permission.MANAGE_STUDENTS,
        Permission.MANAGE_GROUP,
        Permission.ATTENDANCE_VIEW,
        Permission.ATTENDANCE_WRITE,
        Permission.PUBLISH_COURSE,
        Permission.MANAGE_SCHEDULE,
        Permission.MANAGE_CONTENT,
        Permission.VIEW_PUBLIC,
        Permission.VIEW_PUBLIC_PROJECTS,
    }),
    PlatformRole.DEPARTMENT_HEAD: frozenset({
        Permission.VIEW_ACADEMICS,
        Permission.VIEW_STUDENT_PRIVATE,
        Permission.MANAGE_GROUP,
        Permission.ATTENDANCE_VIEW,
        Permission.ATTENDANCE_WRITE,
        Permission.PUBLISH_COURSE,
        Permission.MANAGE_SCHEDULE,
        Permission.MANAGE_CONTENT,
        Permission.VIEW_PUBLIC,
        Permission.VIEW_PUBLIC_PROJECTS,
    }),
    PlatformRole.INSTRUCTOR: frozenset({
        Permission.VIEW_ACADEMICS,
        Permission.MANAGE_GROUP,
        Permission.CREATE_GROUP,
        Permission.ATTENDANCE_VIEW,
        Permission.ATTENDANCE_WRITE,
        Permission.PUBLISH_COURSE,
        Permission.MANAGE_CONTENT,
        Permission.VIEW_PUBLIC,
        Permission.VIEW_PUBLIC_PROJECTS,
        Permission.PROJECT_MANAGE,
    }),
    PlatformRole.REPRESENTATIVE: frozenset({
        Permission.VIEW_ACADEMICS,
        Permission.VIEW_PUBLIC,
        Permission.VIEW_PUBLIC_PROJECTS,
    }),
    PlatformRole.STUDENT: frozenset({
        Permission.VIEW_ACADEMICS,
        Permission.USE_AI,
        Permission.VIEW_PUBLIC,
        Permission.VIEW_PUBLIC_PROJECTS,
        Permission.PROJECT_MANAGE,
    }),
    PlatformRole.DEVELOPER: frozenset({Permission.VIEW_PUBLIC, Permission.VIEW_PUBLIC_PROJECTS}),
    PlatformRole.ALUMNI: frozenset({Permission.VIEW_PUBLIC, Permission.VIEW_PUBLIC_PROJECTS, Permission.PROJECT_MANAGE}),
    PlatformRole.GUEST: frozenset({Permission.VIEW_PUBLIC, Permission.VIEW_PUBLIC_PROJECTS}),
}


class AccessPolicy:
    """Central policy service; role defaults may be overridden per tenant."""

    def __init__(self, tenant_overrides: Mapping[str, Mapping[str, Iterable[Permission]]] | None = None):
        self.tenant_overrides = tenant_overrides or {}

    def permissions_for(self, tenant_id: str, role: PlatformRole) -> frozenset[Permission]:
        base = set(ROLE_DEFAULT_PERMISSIONS.get(role, frozenset()))
        override = self.tenant_overrides.get(tenant_id, {}).get(role.value)
        if override is None:
            return frozenset(base)
        return frozenset(override)

    def build_context(
        self,
        *,
        tenant_id: str,
        user_id: str,
        role: PlatformRole,
        student_status: StudentStatus | None = None,
        extra_permissions: Iterable[Permission] = (),
    ) -> AccessContext:
        permissions = set(self.permissions_for(tenant_id, role))
        permissions.update(extra_permissions)
        # Graduated/withdrawn students must never inherit active-student AI or academic permissions.
        if role == PlatformRole.STUDENT and student_status != StudentStatus.ACTIVE:
            permissions.discard(Permission.USE_AI)
            permissions.discard(Permission.VIEW_ACADEMICS)
        return AccessContext(
            tenant_id=tenant_id,
            user_id=user_id,
            role=role,
            student_status=student_status,
            permissions=frozenset(permissions),
        )

    @staticmethod
    def require(context: AccessContext, permission: Permission) -> None:
        if permission not in context.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied: {permission.value}",
            )

    @staticmethod
    def require_active_student(context: AccessContext) -> None:
        if not context.is_active_student:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This feature is available only to currently enrolled students.",
            )


def request_access_context(request: Request) -> AccessContext:
    """Read the authenticated context prepared by authentication middleware.

    This helper deliberately fails closed: missing identity is not treated as a guest
    for private endpoints. Public endpoints should explicitly use the public policy.
    """
    context = getattr(request.state, "access_context", None)
    if context is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    return context
