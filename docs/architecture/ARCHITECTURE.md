# Comprehensive System Architecture: University Digital Infrastructure Platform

This document describes the design, data isolation, and operational layers of the University Digital Infrastructure Platform.

## 1. Multi-Tenant Data Isolation Strategy
- **Layer 1 (API Gateway)**: Subdomain / JWT Tenant resolution (`tenant_id`).
- **Layer 2 (Application Middleware)**: Request-scoped tenant context injection.
- **Layer 3 (Database Policies)**: PostgreSQL Row-Level Security (`USING (tenant_id = current_setting('app.current_tenant'))`).
- **Layer 4 (Storage)**: S3 object storage prefixed by `/{tenant_id}/...`.

## 2. Granular RBAC Matrix
Every operation is evaluated against:
`Role + Permission + Resource + Tenant`

## 3. Sovereign AI & Agent Gateway
- Zero multi-tenant leakage in vector index and prompts.
- Tool calling gateway verifies user permissions before invoking any API mutation.
- Sensitive write operations enforce explicit user confirmation dialogues.
