from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from app.core.access_control import AccessContext, Permission


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str
    requires_confirmation: bool = False


SENSITIVE_WRITE_PERMISSIONS = {
    Permission.ATTENDANCE_WRITE,
    Permission.PUBLISH_COURSE,
    Permission.MANAGE_STUDENTS,
    Permission.MANAGE_GROUP,
    Permission.MANAGE_SCHEDULE,
    Permission.MANAGE_UNIVERSITY,
    Permission.PROJECT_MANAGE,
}


class AuthorizationService:
    def decide(self, context: AccessContext, permission: Permission, *, write: bool = False) -> AuthorizationDecision:
        if permission not in context.permissions:
            return AuthorizationDecision(False, f"Missing permission: {permission.value}")
        if write and permission in SENSITIVE_WRITE_PERMISSIONS:
            return AuthorizationDecision(True, "Authorized but explicit confirmation is required", True)
        return AuthorizationDecision(True, "Authorized")

    def ensure_tool_allowed(
        self,
        context: AccessContext,
        permission: Permission,
        *,
        write: bool,
        required_permissions: Iterable[Permission] = (),
    ) -> AuthorizationDecision:
        for required in required_permissions:
            if required not in context.permissions:
                return AuthorizationDecision(False, f"Missing prerequisite permission: {required.value}")
        return self.decide(context, permission, write=write)
