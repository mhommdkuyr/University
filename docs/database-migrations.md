# Production database migrations

Production uses PostgreSQL with TLS and Alembic. The application must not create its schema automatically in production.

## Apply

From the repository root:

```bash
cd services/api
alembic upgrade head
```

Required environment:

```text
ENVIRONMENT=production
DATABASE_URL=postgresql+asyncpg://...
DATABASE_SSL_MODE=require
AUTO_CREATE_SCHEMA=false
```

The initial migration creates the tenant-scoped tables and enables PostgreSQL Row-Level Security on tenant-owned tables.

The application sets a transaction-local tenant identifier for PostgreSQL sessions before tenant-scoped queries. The policy compares the row's `tenant_id` with `current_setting('app.tenant_id', true)`.

Do not run the migration against a SQLite staging database. SQLite remains available for lightweight local/staging boot tests only.

## Release procedure

1. Take a database backup/snapshot.
2. Apply Alembic migrations.
3. Start the new application version.
4. Verify health, authentication, tenant isolation and a representative academic write.
5. Review audit events and error rate before accepting the release.

Rollback must be tested from a backup/restore procedure rather than assuming every schema migration is automatically reversible.
