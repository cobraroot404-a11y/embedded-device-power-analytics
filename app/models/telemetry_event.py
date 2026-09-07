import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class TelemetryEvent(Base):
    """Raw telemetry — the authoritative, append-only time-series source.

    A TimescaleDB hypertable partitioned on `time` (the device-reported event
    timestamp, not ingestion time). `time` is intentionally part of the unique
    constraint because Timescale requires the partitioning column in any
    unique index on a hypertable; `message_id` is globally unique in practice
    so this still gives us robust dedup via ON CONFLICT DO NOTHING.
    """

    __tablename__ = "telemetry_events"
    __table_args__ = (
        UniqueConstraint("device_id", "message_id", "time", name="uq_telemetry_dedup"),
    )

    # Composite PK (id, time): TimescaleDB requires the partitioning column
    # (`time`) in every unique index on a hypertable, including the PK.
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    time: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    device_id: Mapped[str] = mapped_column(String, nullable=False)
    message_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    state: Mapped[str] = mapped_column(String, nullable=False)
    battery_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    power_watts: Mapped[float | None] = mapped_column(Float, nullable=True)
    boot_id: Mapped[str | None] = mapped_column(String, nullable=True)
    ingested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
