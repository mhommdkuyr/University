-- Tenant-aware university identity, role policy, and adaptive feature configuration.

CREATE TABLE IF NOT EXISTS student_identity_bindings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    university_student_number VARCHAR(100) NOT NULL,
    source_system VARCHAR(100) NOT NULL,
    external_subject VARCHAR(255),
    identity_status VARCHAR(30) NOT NULL DEFAULT 'verified'
        CHECK (identity_status IN ('pending', 'verified', 'revoked')),
    last_verified_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, university_student_number),
    UNIQUE (tenant_id, source_system, external_subject)
);

CREATE TABLE IF NOT EXISTS tenant_role_policies (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    role_name VARCHAR(80) NOT NULL,
    permission_name VARCHAR(120) NOT NULL,
    effect VARCHAR(10) NOT NULL DEFAULT 'allow' CHECK (effect IN ('allow', 'deny')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, role_name, permission_name)
);

CREATE TABLE IF NOT EXISTS tenant_features (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    feature_key VARCHAR(100) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT FALSE,
    integration_mode VARCHAR(30) NOT NULL DEFAULT 'platform'
        CHECK (integration_mode IN ('platform', 'external', 'hidden')),
    external_endpoint TEXT,
    configuration JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, feature_key)
);

CREATE TABLE IF NOT EXISTS tenant_ui_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    page_key VARCHAR(120) NOT NULL,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    route VARCHAR(255),
    source VARCHAR(30) NOT NULL DEFAULT 'platform'
        CHECK (source IN ('platform', 'external', 'existing')),
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    UNIQUE (tenant_id, page_key)
);

CREATE TABLE IF NOT EXISTS tenant_role_scopes (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    role_name VARCHAR(80) NOT NULL,
    scope_type VARCHAR(50) NOT NULL,
    scope_id UUID,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, role_name, scope_type, scope_id)
);

CREATE INDEX IF NOT EXISTS idx_identity_bindings_tenant_student
    ON student_identity_bindings(tenant_id, student_id);
CREATE INDEX IF NOT EXISTS idx_role_policies_tenant_role
    ON tenant_role_policies(tenant_id, role_name);
CREATE INDEX IF NOT EXISTS idx_features_tenant
    ON tenant_features(tenant_id);
CREATE INDEX IF NOT EXISTS idx_ui_pages_tenant
    ON tenant_ui_pages(tenant_id);

-- RLS is enabled here so future application code cannot accidentally bypass tenant isolation.
ALTER TABLE student_identity_bindings ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_role_policies ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_features ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_ui_pages ENABLE ROW LEVEL SECURITY;
ALTER TABLE tenant_role_scopes ENABLE ROW LEVEL SECURITY;

CREATE POLICY identity_bindings_tenant_isolation ON student_identity_bindings
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY role_policies_tenant_isolation ON tenant_role_policies
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY features_tenant_isolation ON tenant_features
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY ui_pages_tenant_isolation ON tenant_ui_pages
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);

CREATE POLICY role_scopes_tenant_isolation ON tenant_role_scopes
    USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    WITH CHECK (tenant_id = current_setting('app.current_tenant', true)::uuid);

-- Default platform features. New tenants can override these during onboarding.
-- These rows are templates only; deployment code should copy them for each tenant.
COMMENT ON TABLE tenant_features IS 'Per-university feature switches and integration mode. Existing university pages are not replaced unless the tenant enables the platform feature.';
COMMENT ON TABLE tenant_ui_pages IS 'Per-university page registry discovered during onboarding and environment mapping.';
COMMENT ON TABLE tenant_role_policies IS 'Per-university permission overrides selected by authorized university administrators.';
