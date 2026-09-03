"""Cria tabelas de deputados e execuções de ingestão.

Revision ID: 0001_initial
Revises:
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    status_type = sa.Enum("running", "succeeded", "failed", name="ingestion_run_status")
    status_type.create(op.get_bind(), checkfirst=True)
    ingestion_status = postgresql.ENUM(
        "running", "succeeded", "failed", name="ingestion_run_status", create_type=False
    )

    op.create_table(
        "deputies",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("external_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("party", sa.String(length=50), nullable=False),
        sa.Column("state", sa.String(length=2), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("photo_url", sa.Text(), nullable=True),
        sa.Column("source_url", sa.Text(), nullable=False),
        sa.Column("source_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("external_id"),
    )
    op.create_index("ix_deputies_name", "deputies", ["name"])
    op.create_index("ix_deputies_party", "deputies", ["party"])
    op.create_index("ix_deputies_state", "deputies", ["state"])
    op.create_index("ix_deputies_party_state", "deputies", ["party", "state"])

    op.create_table(
        "ingestion_runs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=255), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", ingestion_status, nullable=False),
        sa.Column("records_received", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_inserted", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_updated", sa.Integer(), server_default="0", nullable=False),
        sa.Column("records_rejected", sa.Integer(), server_default="0", nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("ingestion_runs")
    op.drop_index("ix_deputies_party_state", table_name="deputies")
    op.drop_index("ix_deputies_state", table_name="deputies")
    op.drop_index("ix_deputies_party", table_name="deputies")
    op.drop_index("ix_deputies_name", table_name="deputies")
    op.drop_table("deputies")
    sa.Enum(name="ingestion_run_status").drop(op.get_bind(), checkfirst=True)
