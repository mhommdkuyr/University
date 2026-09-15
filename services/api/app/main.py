from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.middleware import TenantMiddleware
from app.modules.auth.router import router as auth_router
from app.modules.tenants.router import router as tenants_router
from app.modules.academics.router import router as academics_router
from app.modules.projects.router import router as projects_router
from app.modules.audit.router import router as audit_router
from app.modules.search.router import router as search_router
from app.modules.ai_agent.router import router as ai_agent_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.0.0",
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(TenantMiddleware)

# API v1 Routers
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication & SSO"])
app.include_router(tenants_router, prefix="/api/v1/tenants", tags=["Tenants Management"])
app.include_router(academics_router, prefix="/api/v1/academics", tags=["Academic Core"])
app.include_router(projects_router, prefix="/api/v1/projects", tags=["Student Projects & Research"])
app.include_router(search_router, prefix="/api/v1/search", tags=["Vector & Semantic Search"])
app.include_router(ai_agent_router, prefix="/api/v1/ai", tags=["AI Assistant & Agents"])
app.include_router(audit_router, prefix="/api/v1/audit", tags=["Audit & Security Logs"])

@app.get("/api/v1/health", tags=["System"])
async def health_check():
    return {
        "status": "online",
        "version": "1.0.0",
        "architecture": "Modular Monolith",
        "service": "University Digital Infrastructure API"
    }
