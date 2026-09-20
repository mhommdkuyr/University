from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import text

from app.core.config import settings
from app.core.database import SessionLocal, engine, init_db
from app.core.middleware import TenantMiddleware
from app.modules.academics.router import router as academics_router
from app.modules.ai_agent.router import router as ai_agent_router
from app.modules.audit.router import router as audit_router
from app.modules.developer.router import router as developer_router
from app.modules.auth.router import router as auth_router
from app.modules.features.router import router as features_router
from app.modules.identity.router import router as identity_router
from app.modules.projects.router import router as projects_router
from app.modules.roles.router import router as roles_router
from app.modules.search.router import router as search_router
from app.modules.teaching.router import router as teaching_router
from app.modules.tenants.router import router as tenants_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.ENVIRONMENT == "production" and settings.JWT_SECRET == "development_secret_key_change_in_production":
        raise RuntimeError("JWT_SECRET must be changed in production")
    await init_db()
    yield
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="2.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json",
    lifespan=lifespan,
)

origins = [item.strip() for item in settings.CORS_ORIGINS.split(",") if item.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Tenant-ID", "X-API-Key"],
)
app.add_middleware(TenantMiddleware)


@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication & SSO"])
app.include_router(identity_router, prefix="/api/v1/identity", tags=["University Identity"])
app.include_router(tenants_router, prefix="/api/v1/tenants", tags=["Tenants Management"])
app.include_router(roles_router, prefix="/api/v1/roles", tags=["Role Policies"])
app.include_router(features_router, prefix="/api/v1/features", tags=["Adaptive University Features"])
app.include_router(academics_router, prefix="/api/v1/academics", tags=["Academic Core"])
app.include_router(teaching_router, prefix="/api/v1/teaching", tags=["Teaching & Attendance"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Student Projects & Research"])
app.include_router(search_router, prefix="/api/v1/search", tags=["Search"])
app.include_router(ai_agent_router, prefix="/api/v1/ai", tags=["AI Assistant & Agents"])
app.include_router(audit_router, prefix="/api/v1/audit", tags=["Audit & Security Logs"])
app.include_router(developer_router, prefix="/api/v1/developer", tags=["Developer API Keys"])


@app.get("/", tags=["System"])
async def root():
    return {"service": "University Digital Infrastructure API", "docs": "/api/v1/docs", "health": "/api/v1/health"}


@app.head("/", include_in_schema=False)
async def root_head():
    return Response(status_code=200)


@app.get("/api/v1/health", tags=["System"])
async def health_check():
    database = "unknown"
    try:
        async with SessionLocal() as session:
            await session.execute(text("SELECT 1"))
        database = "ok"
    except Exception:
        database = "unavailable"

    return {
        "status": "online" if database == "ok" else "degraded",
        "version": "2.0.0",
        "service": "University Digital Infrastructure API",
        "database": database,
    }
