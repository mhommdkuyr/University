# Commercial readiness

The platform is a multi-tenant university digital layer. Each institution configures its identity source, enrollment status source, branding, enabled modules and role policy.

## Core modules

1. Identity and tenant isolation.
2. Student lifecycle and role policy.
3. Courses, groups, attendance and publishing.
4. Public projects and student public profiles.
5. University administration and feature configuration.
6. Developer API and OpenAPI.
7. AI gateway with authorization before provider access.
8. Audit and operational observability.

## Go-live checklist

- [ ] Connect each university's authoritative identity/enrollment source.
- [ ] Configure production PostgreSQL, backups, RLS verification and migrations.
- [ ] Configure Redis and rate limits.
- [ ] Configure TLS, domain, reverse proxy and CORS.
- [ ] Store secrets in the deployment provider.
- [ ] Configure AI provider/model and spending limits.
- [ ] Run security/penetration testing and dependency scanning.
- [ ] Establish privacy policy, data-retention policy, DPA/contract terms and incident response.
- [ ] Pilot with one university before multi-tenant production rollout.
