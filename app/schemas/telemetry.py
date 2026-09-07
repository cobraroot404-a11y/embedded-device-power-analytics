import re
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

DEVICE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{0,63}$")


class DeviceState(StrEnum):
    ON = "ON"
    SLEEP = "SLEEP"
    OFF = "OFF"


class TelemetryEventIn(BaseModel):
    """Wire schema for an inbound MQTT telemetry payload.

    Any field that fails validation raises pydantic.ValidationError; the
    ingestion layer maps the failing field to a rejection reason used for
    metrics and anomaly bookkeeping, rather than duplicating these rules.
    """

    message_id: UUID
    device_id: str
    timestamp: datetime
    state: DeviceState
    battery_percent: float | None = Field(default=None)
    power_watts: float | None = Field(default=None)
    boot_id: str | None = Field(default=None)

    @field_validator("device_id")
    @classmethod
    def validate_device_id(cls, v: str) -> str:
        if not DEVICE_ID_PATTERN.match(v):
            raise ValueError("device_id must be 1-64 alphanumeric/underscore/hyphen characters")
        return v

    @field_validator("timestamp")
    @classmethod
    def validate_timestamp(cls, v: datetime) -> datetime:
        if v.tzinfo is None:
            raise ValueError("timestamp must be timezone-aware")
        return v.astimezone(UTC)

    @field_validator("battery_percent")
    @classmethod
    def validate_battery(cls, v: float | None) -> float | None:
        if v is not None and not (0.0 <= v <= 100.0):
            raise ValueError("battery_percent must be between 0 and 100")
        return v

    @field_validator("power_watts")
    @classmethod
    def validate_power(cls, v: float | None) -> float | None:
        if v is not None and v < 0.0:
            raise ValueError("power_watts must not be negative")
        return v
