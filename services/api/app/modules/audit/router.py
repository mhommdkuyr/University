from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.access_control import Permission, PlatformRole, request_access_context
from app.core.database import AuditLog, get_session


router = APIRouter()


class AuditEntry(BaseModel):
    id: str
    action: str
    resource_type: str
    status: str
    timestamp: str


@router.get("/logs", response_model=list[AuditEntry])
async def get_audit_logs(
    request: Request,
    session: AsyncSession = Depends(get_session),
):
    context = request_access_context(request)
    allowed = context.role == PlatformRole.PLATFORM_ADMIN or Permission.MANAGE_UNIVERSITY in context.permissions
    if not allowed:
        raise HTTPException(status_code=403, detail="Audit access denied")

    rows = (
        await session.scalars(
            select(AuditLog)
            .where(AuditLog.tenant_id == context.tenant_id)
            .order_by(AuditLog.timestamp.desc())
            .limit(200)
        )
    ).all()

    return [
        AuditEntry(
            id=row.id,
            action=row.action,
            resource_type=row.resource_type,
            status=row.status,
            timestamp=row.timestamp.isoformat(),
        )
        for row in rows
    ]
