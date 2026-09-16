"""Helpers for binding a validated tenant to the current PostgreSQL transaction.

The application must call this after authenticating the user and before accessing
RLS-protected tenant data. It intentionally does not trust a raw client header as
an authorization decision.
"""
from __future__ import annotations

from typing import Any


async def set_current_tenant(connection: Any, tenant_id: str) -> None:
    """Set the transaction-local RLS tenant context."""
    if not tenant_id:
        raise ValueError("tenant_id is required")
    await connection.execute("SELECT set_config('app.current_tenant', :tenant_id, true)", {"tenant_id": tenant_id})
