import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.ingestion.pipeline import process_message
from app.models.anomaly import Anomaly
from app.models.device import Device
from app.models.telemetry_event import TelemetryEvent

pytestmark = pytest.mark.asyncio

SETTINGS = get_settings()


def _topic(device_id: str) -> str:
    return f"devices/{device_id}/telemetry"


def _payload(device_id: str, timestamp: datetime, **overrides) -> bytes:
    data = {
        "message_id": str(uuid.uuid4()),
        "device_id": device_id,
        "timestamp": timestamp.isoformat(),
        "state": "ON",
        "battery_percent": 80.0,
        "power_watts": 5.0,
        "boot_id": "boot-a",
    }
    data.update(overrides)
    return json.dumps(data).encode()


async def test_valid_message_persists_event_and_device(db_session) -> None:
    now = datetime.now(UTC)
    await process_message(db_session, SETTINGS, _payload("MIF-100", now), _topic("MIF-100"))

    events = (await db_session.execute(select(TelemetryEvent))).scalars().all()
    devices = (await db_session.execute(select(Device))).scalars().all()
    assert len(events) == 1
    assert len(devices) == 1
    assert devices[0].device_id == "MIF-100"
    assert devices[0].last_state == "ON"


async def test_new_device_registers_without_prior_configuration(db_session) -> None:
    now = datetime.now(UTC)
    await process_message(db_session, SETTINGS, _payload("BRAND-NEW-999", now), _topic("BRAND-NEW-999"))
    device = await db_session.get(Device, "BRAND-NEW-999")
    assert device is not None


async def test_duplicate_message_id_does_not_double_insert(db_session) -> None:
    now = datetime.now(UTC)
    message_id = str(uuid.uuid4())
    payload = _payload("MIF-101", now, message_id=message_id)

    await process_message(db_session, SETTINGS, payload, _topic("MIF-101"))
    await process_message(db_session, SETTINGS, payload, _topic("MIF-101"))  # exact resend

    events = (await db_session.execute(select(TelemetryEvent))).scalars().all()
    assert len(events) == 1


async def test_malformed_json_does_not_persist_or_raise(db_session) -> None:
    await process_message(db_session, SETTINGS, b"not json", _topic("MIF-102"))
    events = (await db_session.execute(select(TelemetryEvent))).scalars().all()
    assert len(events) == 0


async def test_malformed_message_does_not_block_other_devices(db_session) -> None:
    now = datetime.now(UTC)
    await process_message(db_session, SETTINGS, b"garbage", _topic("MIF-103"))
    await process_message(db_session, SETTINGS, _payload("MIF-104", now), _topic("MIF-104"))

    device = await db_session.get(Device, "MIF-104")
    assert device is not None


async def test_reboot_detected_and_recorded_as_anomaly(db_session) -> None:
    t1 = datetime.now(UTC)
    t2 = t1 + timedelta(minutes=5)
    await process_message(db_session, SETTINGS, _payload("MIF-105", t1, boot_id="boot-a"), _topic("MIF-105"))
    await process_message(db_session, SETTINGS, _payload("MIF-105", t2, boot_id="boot-b"), _topic("MIF-105"))

    anomalies = (
        (await db_session.execute(select(Anomaly).where(Anomaly.device_id == "MIF-105"))).scalars().all()
    )
    reboot_anomalies = [a for a in anomalies if a.anomaly_type == "reboot"]
    assert len(reboot_anomalies) == 1
    assert reboot_anomalies[0].details["previous_boot_id"] == "boot-a"
    assert reboot_anomalies[0].details["new_boot_id"] == "boot-b"


async def test_low_battery_recorded_as_anomaly(db_session) -> None:
    now = datetime.now(UTC)
    payload = _payload("MIF-106", now, battery_percent=5.0)
    await process_message(db_session, SETTINGS, payload, _topic("MIF-106"))

    anomalies = (
        (await db_session.execute(select(Anomaly).where(Anomaly.device_id == "MIF-106"))).scalars().all()
    )
    assert any(a.anomaly_type == "low_battery" for a in anomalies)


async def test_communication_gap_recorded_as_anomaly(db_session) -> None:
    t1 = datetime.now(UTC)
    t2 = t1 + timedelta(minutes=SETTINGS.gap_threshold_minutes + 10)
    await process_message(db_session, SETTINGS, _payload("MIF-107", t1), _topic("MIF-107"))
    await process_message(db_session, SETTINGS, _payload("MIF-107", t2), _topic("MIF-107"))

    anomalies = (
        (await db_session.execute(select(Anomaly).where(Anomaly.device_id == "MIF-107"))).scalars().all()
    )
    assert any(a.anomaly_type == "communication_gap" for a in anomalies)


async def test_out_of_order_message_still_persists(db_session) -> None:
    t1 = datetime.now(UTC)
    t_earlier = t1 - timedelta(minutes=10)
    await process_message(db_session, SETTINGS, _payload("MIF-108", t1), _topic("MIF-108"))
    await process_message(db_session, SETTINGS, _payload("MIF-108", t_earlier), _topic("MIF-108"))

    events = (
        (await db_session.execute(select(TelemetryEvent).where(TelemetryEvent.device_id == "MIF-108")))
        .scalars()
        .all()
    )
    assert len(events) == 2
