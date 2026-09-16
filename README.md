# University Digital Infrastructure Platform & University API

A multi-tenant SaaS digital infrastructure platform for higher-education institutions. The platform transforms traditional university operations into an API-first, AI-enabled, and Agentic ecosystem.

## 🚀 Key Architecture Pillars
1. **Multi-Tenant SaaS Foundation**: Complete isolation across universities via Tenant Resolution Middleware and PostgreSQL Row-Level Security (RLS).
2. **Modular Monolith**: Clean domain boundaries (`auth`, `tenants`, `academics`, `projects`, `audit`, `search`, `ai_agent`, `identity`, `roles`, `features`, `teaching`) designed for seamless microservice extraction.
3. **Sovereign AI & Agent Gateway**: Tenant-scoped RAG, model routing, and tool execution with strict multi-layer permission validation. The model may propose an action; deterministic authorization decides whether it can run.
4. **University Identity & Lifecycle Access**: Student access is tied to the university's authoritative student record and enrollment status. Active students can receive academic/AI privileges; graduates and inactive students are restricted to the public/alumni surface according to university policy.
5. **Adaptive University Environment**: The platform discovers what systems and pages a university already has and supports each module as platform-managed, externally integrated, or hidden. Existing university systems are never replaced merely because a platform module exists.
6. **Teaching & Delegated Roles**: Instructor permissions cover groups, attendance, course publishing and related teaching operations. The representative role is configurable per university by authorized university leadership.
7. **Developer-First Ecosystem**: Standardized REST API (/api/v1), OpenAPI 3.0 docs, hashed API keys, and event-driven Webhooks.
8. **SEO-Optimized Public Showcase**: Server-renderable and indexable public pages for student graduation projects, research papers, student profiles and campus activities.

## 📂 Monorepo Structure
```text
University/
├── apps/
│   ├── web/                    # Public SEO-ready university web pages
│   ├── university-dashboard/   # University operations & faculty management
│   ├── student-portal/         # Active student academic workspace & project submissions
│   ├── developer-portal/       # API keys, interactive API docs, webhook settings
│   └── admin-dashboard/        # Platform-level SaaS management & AI routing
├── services/
│   └── api/                    # Core Modular Monolith API service (FastAPI)
├── packages/
│   ├── database/               # SQL migrations & RLS policies
│   └── shared/                 # Shared types, schemas, and utilities
├── infrastructure/
│   └── docker/                 # Docker Compose & local dev environment
└── docs/
    ├── architecture/           # System design & API specifications
    ├── authorization-and-roles.md
    ├── adaptive-university-onboarding.md
    └── implementation-status.md
```

## 🛠️ Quickstart with Docker
```bash
# 1. Start database, cache and core services
cd infrastructure/docker
docker-compose up -d

# 2. Access OpenAPI documentation
open http://localhost:8000/api/v1/docs
```

## 🔐 Current access model
- The university student number is an integration identifier, not a password.
- The authoritative university source determines the student's current status.
- AI access is restricted to currently active students in the student role by default.
- Graduates and inactive students do not inherit active-student academic/AI permissions.
- Public visitors can access only intentionally published public content.
- Sensitive writes are designed to require explicit confirmation after deterministic authorization.

See `docs/authorization-and-roles.md` and `docs/adaptive-university-onboarding.md` for the detailed model.

## ⚠️ Production note
This branch establishes the domain contracts, database structures, access-control primitives, and API surfaces. University-specific identity adapters, database repositories, full authentication integration, transaction-local RLS wiring across all existing tables, and complete frontend implementation are still required before production deployment.
