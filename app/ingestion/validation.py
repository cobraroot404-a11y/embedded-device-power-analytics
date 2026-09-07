import json
import re

from pydantic import ValidationError

from app.schemas.telemetry import TelemetryEventIn

TOPIC_PATTERN = re.compile(r"^devices/([^/]+)/telemetry$")

# Maps a pydantic field location to a stable, low-cardinality rejection reason
# used as the `reason` label on telemetry_messages_rejected_total.
_FIELD_REASON = {
    "message_id": "invalid_message_id",
    "device_id": "invalid_device_id",
    "timestamp": "invalid_timestamp",
    "state": "invalid_state",
    "battery_percent": "invalid_battery",
    "power_watts": "invalid_power",
    "boot_id": "invalid_boot_id",
}


class RejectedMessage(Exception):
    def __init__(self, reason: str, detail: str):
        self.reason = reason
        self.detail = detail
        super().__init__(detail)


def extract_device_id_from_topic(topic: str) -> str:
    match = TOPIC_PATTERN.match(topic)
    if not match:
        raise RejectedMessage("invalid_topic", f"topic '{topic}' does not match devices/{{id}}/telemetry")
    return match.group(1)


def parse_and_validate(raw_payload: bytes, topic: str) -> TelemetryEventIn:
    """Parses and validates a raw MQTT payload against the telemetry schema.

    Raises RejectedMessage with a stable reason code on any failure. Never
    raises an unhandled exception — callers can rely on catching exactly
    RejectedMessage for all validation failures.
    """
    topic_device_id = extract_device_id_from_topic(topic)

    try:
        data = json.loads(raw_payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise RejectedMessage("invalid_json", str(exc)) from exc

    if not isinstance(data, dict):
        raise RejectedMessage("invalid_json", "payload is not a JSON object")

    try:
        event = TelemetryEventIn.model_validate(data)
    except ValidationError as exc:
        first_error = exc.errors()[0]
        field_name = str(first_error["loc"][0]) if first_error.get("loc") else "unknown"
        reason = _FIELD_REASON.get(field_name, "schema_error")
        raise RejectedMessage(reason, str(exc)) from exc

    if event.device_id != topic_device_id:
        raise RejectedMessage(
            "topic_device_mismatch",
            f"payload device_id '{event.device_id}' != topic device '{topic_device_id}'",
        )

    return event
