from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.anomalies import detect_abnormal_power, detect_low_battery
from app.core.config import Settings
from app.core.logging import get_logger
from app.core.metrics import (
    device_communication_gaps_total,
    device_reboots_total,
    telemetry_duplicates_total,
    telemetry_messages_rejected_total,
    telemetry_messages_valid_total,
    telemetry_out_of_order_total,
)
from app.ingestion.validation import RejectedMessage, parse_and_validate
from app.services import telemetry_repository as repo

logger = get_logger(__name__)


async def process_message(
    session: AsyncSession, settings: Settings, raw_payload: bytes, topic: str
) -> None:
    """Runs one MQTT message through validation, reliability checks and
    persistence. Never raises — malformed or unexpected content is logged and
    metriced, and one bad message can never interrupt processing of the next
    (from this device or any other)."""
    try:
        event = parse_and_validate(raw_payload, topic)
    except RejectedMessage as exc:
        telemetry_messages_rejected_total.labels(reason=exc.reason).inc()
        logger.warning("telemetry_rejected", reason=exc.reason, detail=exc.detail, topic=topic)
        return

    now = datetime.now(UTC)
    device = await repo.get_device(session, event.device_id)

    is_new_tip = device is None or event.timestamp > device.last_seen
    if device is not None and event.timestamp < device.last_seen:
        telemetry_out_of_order_total.inc()

    gap_seconds: float | None = None
    is_reboot = False
    previous_boot_id: str | None = None
    if device is not None and is_new_tip:
        gap = event.timestamp - device.last_seen
        if gap > timedelta(seconds=settings.gap_threshold_seconds):
            gap_seconds = gap.total_seconds()
        # Captured now, before upsert_device below mutates this same
        # session-identity-mapped `device` object's last_boot_id in place.
        previous_boot_id = device.last_boot_id
        is_reboot = bool(previous_boot_id) and bool(event.boot_id) and previous_boot_id != event.boot_id

    baseline_power = None
    if event.power_watts is not None:
        baseline_power = await repo.get_recent_average_power(session, event.device_id, event.state.value)

    inserted = await repo.insert_event(
        session,
        message_id=event.message_id,
        device_id=event.device_id,
        time=event.timestamp,
        state=event.state.value,
        battery_percent=event.battery_percent,
        power_watts=event.power_watts,
        boot_id=event.boot_id,
        ingested_at=now,
    )

    if not inserted:
        telemetry_duplicates_total.inc()
        logger.info("telemetry_duplicate", device_id=event.device_id, message_id=str(event.message_id))
        await session.commit()
        return

    telemetry_messages_valid_total.inc()
    await repo.upsert_device(
        session,
        device_id=event.device_id,
        event_time=event.timestamp,
        state=event.state.value,
        boot_id=event.boot_id,
    )

    if gap_seconds is not None:
        device_communication_gaps_total.inc()
        await repo.insert_anomaly(
            session,
            device_id=event.device_id,
            anomaly_type="communication_gap",
            detected_at=now,
            event_time=event.timestamp,
            details={"gap_seconds": gap_seconds},
        )

    if is_reboot:
        device_reboots_total.inc()
        await repo.insert_anomaly(
            session,
            device_id=event.device_id,
            anomaly_type="reboot",
            detected_at=now,
            event_time=event.timestamp,
            details={"previous_boot_id": previous_boot_id, "new_boot_id": event.boot_id},
        )

    if event.battery_percent is not None:
        finding = detect_low_battery(
            event.device_id, event.battery_percent, settings, event.timestamp, now
        )
        if finding:
            await repo.insert_anomaly(
                session,
                device_id=event.device_id,
                anomaly_type=finding.anomaly_type,
                detected_at=finding.detected_at,
                event_time=finding.event_time,
                details=finding.details,
            )

    if event.power_watts is not None and baseline_power is not None:
        finding = detect_abnormal_power(
            event.device_id, event.power_watts, baseline_power, settings, event.timestamp, now
        )
        if finding:
            await repo.insert_anomaly(
                session,
                device_id=event.device_id,
                anomaly_type=finding.anomaly_type,
                detected_at=finding.detected_at,
                event_time=finding.event_time,
                details=finding.details,
            )

    await session.commit()
