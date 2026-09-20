"""Initial University platform schema with tenant isolation.

Revision ID: 0001_initial
Revises:
Create Date: 2026-09-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


TENANT_TABLES = [
    "users",
    "projects",
    "courses",
    "student_groups",
    "attendance_records",
    "role_policies",
    "feature_policies",
    "audit_logs",
]


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=100), nullable=False),
        sa.Column("plan", sa.String(length=50), nullable=False, server_default="starter"),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("slug", name="uq_tenants_slug"),
    )
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.Text(), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="student"),
        sa.Column("student_status", sa.String(length=30), nullable=True),
        sa.Column("student_number", sa.String(length=100), nullable=True),
        sa.Column("full_name", sa.String(length=255), nullable=False, server_default=""),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("tenant_id", "email", name="uq_users_tenant_email"),
        sa.UniqueConstraint("tenant_id", "student_number", name="uq_users_tenant_student_number"),
    )
    op.create_index("ix_users_tenant_id", "users", ["tenant_id"])
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_role", "users", ["role"])
    op.create_index("ix_users_student_number", "users", ["student_number"])

    op.create_table(
        "projects",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("owner_id", sa.String(length=64), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=160), nullable=False),
        sa.Column("department", sa.String(length=160), nullable=False, server_default=""),
        sa.Column("status", sa.String(length=40), nullable=False, server_default="draft"),
        sa.Column("description", sa.Text(), nullable=False, server_default=""),
        sa.Column("public_url", sa.String(length=500), nullable=False, server_default=""),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.UniqueConstraint("tenant_id", "slug", name="uq_projects_tenant_slug"),
    )
    op.create_index("ix_projects_tenant_id", "projects", ["tenant_id"])
    op.create_index("ix_projects_status", "projects", ["status"])

    op.create_table(
        "courses",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("credits", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("content", sa.Text(), nullable=False, server_default=""),
        sa.Column("published", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.UniqueConstraint("tenant_id", "code", name="uq_courses_tenant_code"),
    )
    op.create_index("ix_courses_tenant_id", "courses", ["tenant_id"])

    op.create_table(
        "student_groups",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("course_id", sa.String(length=64), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("student_ids", sa.Text(), nullable=False, server_default="[]"),
    )
    op.create_index("ix_student_groups_tenant_id", "student_groups", ["tenant_id"])
    op.create_index("ix_student_groups_course_id", "student_groups", ["course_id"])

    op.create_table(
        "attendance_records",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("student_id", sa.String(length=64), nullable=False),
        sa.Column("course_id", sa.String(length=64), nullable=False),
        sa.Column("present", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("recorded_by", sa.String(length=64), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_attendance_records_tenant_id", "attendance_records", ["tenant_id"])
    op.create_index("ix_attendance_records_student_id", "attendance_records", ["student_id"])
    op.create_index("ix_attendance_records_course_id", "attendance_records", ["course_id"])

    op.create_table(
        "role_policies",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("role", sa.String(length=50), nullable=False),
        sa.Column("permissions", sa.Text(), nullable=False, server_default="[]"),
        sa.UniqueConstraint("tenant_id", "role", name="uq_role_policies_tenant_role"),
    )
    op.create_index("ix_role_policies_tenant_id", "role_policies", ["tenant_id"])

    op.create_table(
        "feature_policies",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("feature_key", sa.String(length=100), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("integration_mode", sa.String(length=30), nullable=False, server_default="platform"),
        sa.Column("external_endpoint", sa.String(length=500), nullable=True),
        sa.UniqueConstraint("tenant_id", "feature_key", name="uq_features_tenant_key"),
    )
    op.create_index("ix_feature_policies_tenant_id", "feature_policies", ["tenant_id"])

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("actor_id", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("resource_type", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("ix_audit_logs_tenant_id", "audit_logs", ["tenant_id"])
    op.create_index("ix_audit_logs_timestamp", "audit_logs", ["timestamp"])

    for table in TENANT_TABLES:
        op.execute(sa.text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY; ALTER TABLE {table} FORCE ROW LEVEL SECURITY"))
        op.execute(
            sa.text(
                f"CREATE POLICY {table}_tenant_isolation ON {table} "
                f"USING (tenant_id = current_setting('app.tenant_id', true)) "
                f"WITH CHECK (tenant_id = current_setting('app.tenant_id', true))"
            )
        )


def downgrade() -> None:
    for table in reversed(TENANT_TABLES):
        op.execute(sa.text(f"DROP POLICY IF EXISTS {table}_tenant_isolation ON {table}"))
        op.execute(sa.text(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY"))

    for table in reversed(TENANT_TABLES):
        op.drop_table(table)

    op.drop_index("ix_tenants_slug", table_name="tenants")
    op.drop_table("tenants")
