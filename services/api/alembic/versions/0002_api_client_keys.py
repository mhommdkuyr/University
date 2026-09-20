"""Add revocable developer API keys.

Revision ID: 0002_api_client_keys
Revises: 0001_initial
Create Date: 2026-09-20
"""

from alembic import op
import sqlalchemy as sa


revision = "0002_api_client_keys"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "api_client_keys",
        sa.Column("id", sa.String(length=64), primary_key=True),
        sa.Column("tenant_id", sa.String(length=64), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("prefix", sa.String(length=32), nullable=False),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=False, server_default="[]"),
        sa.Column("created_by", sa.String(length=64), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("key_hash", name="uq_api_client_keys_hash"),
    )
    op.create_index("ix_api_client_keys_tenant_id", "api_client_keys", ["tenant_id"])
    op.create_index("ix_api_client_keys_prefix", "api_client_keys", ["prefix"])
    op.create_index("ix_api_client_keys_key_hash", "api_client_keys", ["key_hash"])


def downgrade() -> None:
    op.drop_index("ix_api_client_keys_key_hash", table_name="api_client_keys")
    op.drop_index("ix_api_client_keys_prefix", table_name="api_client_keys")
    op.drop_index("ix_api_client_keys_tenant_id", table_name="api_client_keys")
    op.drop_table("api_client_keys")
