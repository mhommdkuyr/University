# Commercial readiness

The platform is a multi-tenant university digital layer. Each institution configures its identity source, enrollment status source, branding, enabled modules and role policy.

## Core modules implemented

1. Identity and tenant isolation with transaction-scoped tenant context.
2. Student lifecycle and role policy.
3. Courses, groups, attendance and publishing.
4. Public approved projects.
5. University administration and feature configuration.
6. REST/OpenAPI developer surface with revocable, tenant-scoped API keys.
7. AI gateway with deterministic authorization and per-user rate limiting.
8. Audit and operational logs.
9. Optional Frappe Education identity adapter.

## Production hardening implemented

- PostgreSQL TLS configuration.
- Alembic migration chain.
- PostgreSQL Row-Level Security on tenant-owned tables, forced for table-owner sessions.
- Redis-backed distributed rate limiting with in-process fallback.
- Login and AI throttling.
- Security response headers and explicit CORS configuration.
- API credentials are stored as hashes and can be revoked; plaintext is returned only at creation.
- Production schema creation is disabled by default; migrations are the intended schema lifecycle.

## Final go-live gates

These require a real deployment and real university information, so they cannot be honestly marked complete from a demo environment:

- [ ] Connect each university's authoritative identity/enrollment source and test lifecycle changes.
- [ ] Execute Alembic migrations against production-grade PostgreSQL and verify RLS with at least two isolated tenants.
- [ ] Configure a managed Redis instance and verify distributed rate limits across more than one API instance.
- [ ] Configure production TLS, domain, reverse proxy and exact CORS origins.
- [ ] Store all credentials in the deployment provider and perform secret rotation.
- [ ] Configure AI provider/model and explicit spending limits.
- [ ] Run security/penetration testing and dependency scanning.
- [ ] Establish privacy policy, retention schedule, DPA/contract terms and incident response.
- [ ] Pilot the platform with one real university before multi-tenant production rollout.

A staging deployment alone is not a production approval.
