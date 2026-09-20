# University Digital Infrastructure Platform & University API

A multi-tenant SaaS foundation for higher-education institutions. This repository now contains a working FastAPI service, tenant-scoped persistence, role/feature policies, public projects, teaching operations, an AI authorization gateway, and optional university-system adapters.

## Architecture currently implemented

1. **Multi-tenant application isolation**: every core record carries a tenant identifier and service queries are scoped by tenant. PostgreSQL RLS is a production hardening step still required before a high-assurance multi-university launch.
2. **Modular monolith**: domain boundaries include auth, tenants, academics, projects, audit, search, AI, identity, roles, features and teaching.
3. **AI authorization gateway**: active students must pass deterministic authorization before AI use. The gateway supports an OpenAI-compatible provider and model fallback list; external calls remain disabled by default.
4. **University identity lifecycle**: local university records can be checked by student number, and an optional Frappe Education REST adapter can verify an external student record.
5. **Adaptive university features**: a university can select which platform modules are enabled and whether a module is platform-managed or externally integrated.
6. **Teaching and delegated roles**: groups, attendance, course publishing and university-specific role policies are persisted and permission-checked.
7. **Developer API**: REST and OpenAPI are available. API-key issuance, webhook management and event delivery are not yet production modules.
8. **Public showcase**: the public web surface can list approved projects. Rich SEO/server-rendered project profiles remain a production-hardening item.

## Repository

```text
University/
├── apps/
│   ├── web/                    # public Arabic RTL web surface
│   ├── university-dashboard/   # university operations UI
│   ├── student-portal/         # active student UI
│   ├── developer-portal/       # API documentation UI
│   └── admin-dashboard/        # platform administration UI
├── services/
│   └── api/                    # FastAPI modular monolith
├── infrastructure/
│   └── docker/                 # local infrastructure
└── docs/
    ├── commercial-readiness.md
    └── integrations/
        └── frappe-education.md
```

## Local quickstart

```bash
cd services/api
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

For production, use PostgreSQL, a shared Redis instance, TLS, managed secrets and a controlled migration process. Do not enable demo seeding in production.

## Access model

- A university student number is an integration identifier, not a password.
- The university's configured identity source determines current student status.
- Active students can receive academic and AI permissions.
- Graduates/inactive students lose active-student AI and academic permissions by default.
- Public visitors can access only deliberately published project records.
- Sensitive write operations require deterministic permission checks; AI cannot bypass those checks.
- Login and AI routes have rate limiting with a Redis-backed implementation and in-process fallback.

## Current verification

The API has been deployed to a Render staging service from `complete-platform-v2`. The service has successfully built and reached the live state on Python 3.12, and the static public web surface has also reached live state.

Staging intentionally uses SQLite and demo data. It is not the production database. A separate Render PostgreSQL instance exists for staging experiments, but the current Render SQL connector could not establish its required TLS connection, so PostgreSQL connectivity is not claimed as verified here.

## Before commercial production

Use the checklist in `docs/commercial-readiness.md`. The main remaining production gates are:

- PostgreSQL migrations plus transaction-level tenant enforcement/RLS.
- Managed Redis and distributed rate-limit verification.
- Secure production authentication/SSO integration selected per university.
- Complete API-key/webhook/billing modules where required.
- Security testing, dependency scanning, backups/restore drills and incident procedures.
- Production domain, TLS, secret rotation, monitoring and alerting.
- A real pilot university identity/integration test with non-demo data.
