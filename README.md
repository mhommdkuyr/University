# University Digital Infrastructure Platform & University API

A multi-tenant SaaS digital infrastructure platform for higher-education institutions. The platform transforms traditional university operations into an API-first, AI-enabled, and Agentic ecosystem.

## 🚀 Key Architecture Pillars
1. **Multi-Tenant SaaS Foundation**: Complete isolation across universities via Tenant Resolution Middleware and PostgreSQL Row-Level Security (RLS).
2. **Modular Monolith**: Clean domain boundaries (`auth`, `tenants`, `academics`, `projects`, `audit`, `search`, `ai_agent`) designed for seamless microservice extraction.
3. **Sovereign AI & Agent Gateway**: Tenant-scoped RAG, model routing, and tool execution with strict multi-layer permission validation.
4. **Developer-First Ecosystem**: Standardized REST API (/api/v1), OpenAPI 3.0 docs, hashed API keys, and event-driven Webhooks.
5. **SEO-Optimized Public Showcase**: Server-renderable and indexable public pages for student graduation projects, research papers, and campus activities.

## 📂 Monorepo Structure
```text
University/
├── apps/
│   ├── web/                    # Public SEO-ready university web pages
│   ├── university-dashboard/   # University operations & faculty management
│   ├── student-portal/         # Student academic workspace & project submissions
│   ├── developer-portal/       # API keys, interactive Swagger, webhook settings
│   └── admin-dashboard/        # Platform-level SaaS management & AI routing
├── services/
│   └── api/                    # Core Modular Monolith API service (FastAPI)
├── packages/
│   ├── database/               # SQL migrations & RLS policies
│   └── shared/                 # Shared types, schemas, and utilities
├── infrastructure/
│   └── docker/                 # Docker Compose & local dev environment
└── docs/
    └── architecture/           # System design & API specifications
```

## 🛠️ Quickstart with Docker
```bash
# 1. Start database, cache and core services
cd infrastructure/docker
docker-compose up -d

# 2. Access OpenAPI documentation
open http://localhost:8000/api/v1/docs
```
