from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Resolve tenant from header or default
        tenant_id = request.headers.get("X-Tenant-ID")

        path = request.url.path
        if path.startswith("/api/v1/health") or path.startswith("/api/v1/docs") or path.startswith("/api/v1/openapi"):
            return await call_next(request)

        request.state.tenant_id = tenant_id or "default"
        response = await call_next(request)
        return response
