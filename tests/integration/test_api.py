import json
import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.core.config import get_settings
from app.ingestion.pipeline import process_message

SETTINGS = get_settings()


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


async def _seed_device(db_session, device_id: str, now: datetime) -> None:
    topic = f"devices/{device_id}/telemetry"
    on_payload = _payload(device_id, now - timedelta(hours=2), state="ON")
    sleep_payload = _payload(device_id, now - timedelta(hours=1), state="SLEEP")
    await process_message(db_session, SETTINGS, on_payload, topic)
    await process_message(db_session, SETTINGS, sleep_payload, topic)


async def test_health(client) -> None:
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


async def test_ready(client) -> None:
    resp = await client.get("/ready")
    assert resp.status_code == 200


async def test_list_devices_empty(client) -> None:
    resp = await client.get("/devices")
    assert resp.status_code == 200
    assert resp.json() == []


async def test_unknown_device_returns_404(client) -> None:
    resp = await client.get("/devices/DOES-NOT-EXIST")
    assert resp.status_code == 404


async def test_unknown_device_analytics_returns_404(client) -> None:
    resp = await client.get("/devices/DOES-NOT-EXIST/analytics")
    assert resp.status_code == 404


async def test_device_lifecycle(client, db_session) -> None:
    now = datetime.now(UTC)
    await _seed_device(db_session, "MIF-200", now)

    list_resp = await client.get("/devices")
    assert list_resp.status_code == 200
    assert any(d["device_id"] == "MIF-200" for d in list_resp.json())

    detail_resp = await client.get("/devices/MIF-200")
    assert detail_resp.status_code == 200
    assert detail_resp.json()["last_state"] == "SLEEP"

    summary_resp = await client.get("/devices/MIF-200/summary")
    assert summary_resp.status_code == 200
    assert "usage_percent" in summary_resp.json()

    analytics_resp = await client.get("/devices/MIF-200/analytics", params={"period": "daily"})
    assert analytics_resp.status_code == 200
    body = analytics_resp.json()
    assert body["device_id"] == "MIF-200"
    assert body["on_seconds"] >= 0

    anomalies_resp = await client.get("/devices/MIF-200/anomalies")
    assert anomalies_resp.status_code == 200
    assert isinstance(anomalies_resp.json(), list)


async def test_invalid_period_rejected(client, db_session) -> None:
    now = datetime.now(UTC)
    await _seed_device(db_session, "MIF-201", now)
    resp = await client.get("/devices/MIF-201/analytics", params={"period": "yearly"})
    assert resp.status_code == 422


async def test_fleet_summary_with_multiple_devices(client, db_session) -> None:
    now = datetime.now(UTC)
    await _seed_device(db_session, "MIF-202", now)
    await _seed_device(db_session, "MIF-203", now)

    resp = await client.get("/fleet/summary")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_devices"] == 2


async def test_metrics_endpoint_exposes_prometheus_format(client) -> None:
    resp = await client.get("/metrics")
    assert resp.status_code == 200
    assert "text/plain" in resp.headers["content-type"]


@pytest.mark.parametrize("period", ["hourly", "daily", "weekly", "monthly"])
async def test_all_supported_periods_accepted(client, db_session, period) -> None:
    now = datetime.now(UTC)
    await _seed_device(db_session, f"MIF-PERIOD-{period}", now)
    resp = await client.get(f"/devices/MIF-PERIOD-{period}/analytics", params={"period": period})
    assert resp.status_code == 200
