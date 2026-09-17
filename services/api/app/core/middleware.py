from starlette.middleware.base import BaseHTTPMiddleware
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        # Exclude public system and health endpoints from strict tenant requirement
        if path.startswith("/api/v1/health") or path.startswith("/api/v1/docs") or path.startswith("/api/v1/openapi.json"):
            return await call_next(request)

        # Resolve tenant from header or host subdomain
        tenant_id = request.headers.get("X-Tenant-ID")

        # Public showcase and auth endpoints can fall back to 'public' context if header absent
        is_public_endpoint = path.startswith("/api/v1/auth") or path.startswith("/api/v1/projects/public") or path.startswith("/api/v1/search/public")

        if not tenant_id:
            if is_public_endpoint:
                tenant_id = "public"
            else:
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"detail": "Tenant identification missing. X-Tenant-ID header is required."}
                )

        request.state.tenant_id = tenant_id
        response = await call_next(request)
        return response
