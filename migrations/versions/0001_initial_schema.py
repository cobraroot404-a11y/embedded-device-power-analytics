"""initial schema: devices, telemetry_events hypertable, anomalies

Revision ID: 0001
Revises:
Create Date: 2026-09-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")

    op.create_table(
        "devices",
        sa.Column("device_id", sa.String(), primary_key=True),
        sa.Column("first_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_state", sa.String(), nullable=True),
        sa.Column("last_boot_id", sa.String(), nullable=True),
    )

    op.create_table(
        "telemetry_events",
        sa.Column("id", UUID(as_uuid=True), nullable=False),
        sa.Column("time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("device_id", sa.String(), nullable=False),
        sa.Column("message_id", UUID(as_uuid=True), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("battery_percent", sa.Float(), nullable=True),
        sa.Column("power_watts", sa.Float(), nullable=True),
        sa.Column("boot_id", sa.String(), nullable=True),
        sa.Column("ingested_at", sa.DateTime(timezone=True), nullable=False),
        # `time` must be part of the primary key: TimescaleDB requires the
        # partitioning column in every unique index on a hypertable.
        sa.PrimaryKeyConstraint("id", "time"),
        sa.UniqueConstraint("device_id", "message_id", "time", name="uq_telemetry_dedup"),
    )
    op.execute("SELECT create_hypertable('telemetry_events', 'time')")
    op.create_index(
        "ix_telemetry_device_time",
        "telemetry_events",
        ["device_id", sa.text("time DESC")],
    )

    op.create_table(
        "anomalies",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("device_id", sa.String(), nullable=False),
        sa.Column("anomaly_type", sa.String(), nullable=False),
        sa.Column("detected_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("event_time", sa.DateTime(timezone=True), nullable=False),
        sa.Column("details", JSONB(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_anomalies_device_id", "anomalies", ["device_id"])
    op.create_index("ix_anomalies_event_time", "anomalies", ["event_time"])

    # Demonstrates a TimescaleDB continuous aggregate where it genuinely fits:
    # a simple rollup (message counts per device per hour) for the Grafana
    # ingestion-rate panel. Gap/reboot-aware state-duration analytics are
    # deliberately NOT modelled as a continuous aggregate — that logic needs
    # per-event boot_id/gap comparisons the aggregate can't express, so it
    # stays in the Python analytics engine over raw events.
    op.execute(
        """
        CREATE MATERIALIZED VIEW telemetry_hourly_counts
        WITH (timescaledb.continuous) AS
        SELECT
            device_id,
            time_bucket('1 hour', time) AS bucket,
            count(*) AS message_count
        FROM telemetry_events
        GROUP BY device_id, bucket
        WITH NO DATA
        """
    )
    op.execute(
        """
        SELECT add_continuous_aggregate_policy('telemetry_hourly_counts',
            start_offset => INTERVAL '3 hours',
            end_offset => INTERVAL '1 hour',
            schedule_interval => INTERVAL '1 hour')
        """
    )


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS telemetry_hourly_counts CASCADE")
    op.drop_table("anomalies")
    op.drop_table("telemetry_events")
    op.drop_table("devices")
