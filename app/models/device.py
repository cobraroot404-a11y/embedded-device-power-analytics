from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Device(Base):
    """Device registry. Rows are created lazily on first telemetry event —
    new device IDs work without any code change or pre-registration."""

    __tablename__ = "devices"

    device_id: Mapped[str] = mapped_column(String, primary_key=True)
    first_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_seen: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_state: Mapped[str | None] = mapped_column(String, nullable=True)
    last_boot_id: Mapped[str | None] = mapped_column(String, nullable=True)
