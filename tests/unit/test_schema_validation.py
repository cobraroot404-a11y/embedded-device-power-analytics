import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from app.ingestion.validation import RejectedMessage, parse_and_validate
from app.schemas.telemetry import TelemetryEventIn

TOPIC = "devices/MIF-001/telemetry"


def _payload(**overrides) -> dict:
    base = {
        "message_id": str(uuid.uuid4()),
        "device_id": "MIF-001",
        "timestamp": "2026-09-06T10:30:00Z",
        "state": "ON",
        "battery_percent": 82.5,
        "power_watts": 4.7,
        "boot_id": "boot-1",
    }
    base.update(overrides)
    return base


def test_valid_payload_parses() -> None:
    event = TelemetryEventIn.model_validate(_payload())
    assert event.device_id == "MIF-001"
    assert event.state.value == "ON"
    assert event.timestamp.tzinfo is not None


def test_timestamp_normalised_to_utc() -> None:
    event = TelemetryEventIn.model_validate(_payload(timestamp="2026-09-06T10:30:00+02:00"))
    assert event.timestamp.utcoffset().total_seconds() == 0
    assert event.timestamp == datetime(2026, 9, 6, 8, 30, tzinfo=UTC)


def test_naive_timestamp_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryEventIn.model_validate(_payload(timestamp="2026-09-06T10:30:00"))


def test_invalid_state_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryEventIn.model_validate(_payload(state="RUNNING"))


def test_battery_below_zero_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryEventIn.model_validate(_payload(battery_percent=-1))


def test_battery_above_100_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryEventIn.model_validate(_payload(battery_percent=101))


def test_negative_power_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryEventIn.model_validate(_payload(power_watts=-0.1))


def test_invalid_device_id_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryEventIn.model_validate(_payload(device_id=""))


def test_invalid_message_id_rejected() -> None:
    with pytest.raises(ValidationError):
        TelemetryEventIn.model_validate(_payload(message_id="not-a-uuid"))


def test_optional_fields_may_be_absent() -> None:
    payload = _payload()
    del payload["battery_percent"]
    del payload["power_watts"]
    del payload["boot_id"]
    event = TelemetryEventIn.model_validate(payload)
    assert event.battery_percent is None
    assert event.power_watts is None
    assert event.boot_id is None


class TestParseAndValidatePipeline:
    def test_malformed_json_rejected(self) -> None:
        with pytest.raises(RejectedMessage) as exc:
            parse_and_validate(b"not json at all", TOPIC)
        assert exc.value.reason == "invalid_json"

    def test_valid_payload_passes(self) -> None:
        payload = _payload()
        raw = __import__("json").dumps(payload).encode()
        event = parse_and_validate(raw, TOPIC)
        assert event.device_id == "MIF-001"

    def test_topic_device_mismatch_rejected(self) -> None:
        payload = _payload(device_id="MIF-999")
        raw = __import__("json").dumps(payload).encode()
        with pytest.raises(RejectedMessage) as exc:
            parse_and_validate(raw, TOPIC)
        assert exc.value.reason == "topic_device_mismatch"

    def test_malformed_topic_rejected(self) -> None:
        payload = _payload()
        raw = __import__("json").dumps(payload).encode()
        with pytest.raises(RejectedMessage) as exc:
            parse_and_validate(raw, "not/a/telemetry/topic")
        assert exc.value.reason == "invalid_topic"

    def test_rejection_reason_maps_to_field(self) -> None:
        payload = _payload(state="BOGUS")
        raw = __import__("json").dumps(payload).encode()
        with pytest.raises(RejectedMessage) as exc:
            parse_and_validate(raw, TOPIC)
        assert exc.value.reason == "invalid_state"
