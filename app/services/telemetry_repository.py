"""Database access for telemetry events, the device registry, and anomalies.

All queries are parameterised via SQLAlchemy Core/ORM constructs — no raw
string interpolation of externally supplied values.
"""

import uuid
from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.state_duration import TelemetryPoint
from app.models.anomaly import Anomaly
from app.models.device import Device
from app.models.telemetry_event import TelemetryEvent


async def insert_event(
    session: AsyncSession,
    *,
    message_id: uuid.UUID,
    device_id: str,
    time: datetime,
    state: str,
    battery_percent: float | None,
    power_watts: float | None,
    boot_id: str | None,
    ingested_at: datetime,
) -> bool:
    """Inserts a telemetry event, returning False if it was a duplicate.

    Uses INSERT ... ON CONFLICT DO NOTHING against the (device_id, message_id,
    time) unique constraint so duplicate/replayed messages never alter
    downstream analytics, regardless of delivery order or retry count.
    """
    stmt = (
        pg_insert(TelemetryEvent)
        .values(
            id=uuid.uuid4(),
            message_id=message_id,
            device_id=device_id,
            time=time,
            state=state,
            battery_percent=battery_percent,
            power_watts=power_watts,
            boot_id=boot_id,
            ingested_at=ingested_at,
        )
        .on_conflict_do_nothing(constraint="uq_telemetry_dedup")
        .returning(TelemetryEvent.id)
    )
    result = await session.execute(stmt)
    return result.first() is not None


async def get_latest_event_time(session: AsyncSession, device_id: str) -> datetime | None:
    stmt = select(func.max(TelemetryEvent.time)).where(TelemetryEvent.device_id == device_id)
    return (await session.execute(stmt)).scalar_one_or_none()


async def upsert_device(
    session: AsyncSession,
    *,
    device_id: str,
    event_time: datetime,
    state: str,
    boot_id: str | None,
) -> None:
    device = await session.get(Device, device_id)
    if device is None:
        session.add(
            Device(
                device_id=device_id,
                first_seen=event_time,
                last_seen=event_time,
                last_state=state,
                last_boot_id=boot_id,
            )
        )
        return

    if event_time >= device.last_seen:
        device.last_seen = event_time
        device.last_state = state
        device.last_boot_id = boot_id


async def list_devices(session: AsyncSession) -> list[Device]:
    result = await session.execute(select(Device).order_by(Device.device_id))
    return list(result.scalars().all())


async def get_device(session: AsyncSession, device_id: str) -> Device | None:
    return await session.get(Device, device_id)


async def get_points_for_window(
    session: AsyncSession,
    device_id: str,
    window_start: datetime,
    window_end: datetime,
) -> list[TelemetryPoint]:
    """Fetches all events within [window_start, window_end], plus the single
    nearest event just before window_start and just after window_end (if they
    exist), so the analytics engine can correctly bound the first/last
    interval instead of fabricating state at the window's edges."""
    in_window_stmt = (
        select(TelemetryEvent)
        .where(
            TelemetryEvent.device_id == device_id,
            TelemetryEvent.time >= window_start,
            TelemetryEvent.time <= window_end,
        )
        .order_by(TelemetryEvent.time)
    )
    before_stmt = (
        select(TelemetryEvent)
        .where(TelemetryEvent.device_id == device_id, TelemetryEvent.time < window_start)
        .order_by(TelemetryEvent.time.desc())
        .limit(1)
    )
    after_stmt = (
        select(TelemetryEvent)
        .where(TelemetryEvent.device_id == device_id, TelemetryEvent.time > window_end)
        .order_by(TelemetryEvent.time.asc())
        .limit(1)
    )

    in_window = (await session.execute(in_window_stmt)).scalars().all()
    before = (await session.execute(before_stmt)).scalars().one_or_none()
    after = (await session.execute(after_stmt)).scalars().one_or_none()

    events = [*([before] if before else []), *in_window, *([after] if after else [])]
    return [
        TelemetryPoint(time=e.time, state=e.state, boot_id=e.boot_id, power_watts=e.power_watts)
        for e in events
    ]


async def get_recent_average_power(
    session: AsyncSession, device_id: str, state: str, sample_limit: int = 50
) -> float | None:
    subq = (
        select(TelemetryEvent.power_watts)
        .where(
            TelemetryEvent.device_id == device_id,
            TelemetryEvent.state == state,
            TelemetryEvent.power_watts.is_not(None),
        )
        .order_by(TelemetryEvent.time.desc())
        .limit(sample_limit)
        .subquery()
    )
    stmt = select(func.avg(subq.c.power_watts))
    return (await session.execute(stmt)).scalar_one_or_none()


async def insert_anomaly(
    session: AsyncSession,
    *,
    device_id: str,
    anomaly_type: str,
    detected_at: datetime,
    event_time: datetime,
    details: dict,
) -> None:
    session.add(
        Anomaly(
            device_id=device_id,
            anomaly_type=anomaly_type,
            detected_at=detected_at,
            event_time=event_time,
            details=details,
        )
    )


async def list_anomalies(
    session: AsyncSession, device_id: str, limit: int = 100
) -> list[Anomaly]:
    stmt = (
        select(Anomaly)
        .where(Anomaly.device_id == device_id)
        .order_by(Anomaly.event_time.desc())
        .limit(limit)
    )
    return list((await session.execute(stmt)).scalars().all())


async def count_recent_anomalies(session: AsyncSession, since: datetime) -> int:
    stmt = select(func.count()).select_from(Anomaly).where(Anomaly.detected_at >= since)
    return (await session.execute(stmt)).scalar_one()


async def count_anomalies_for_device(session: AsyncSession, device_id: str, since: datetime) -> int:
    stmt = (
        select(func.count())
        .select_from(Anomaly)
        .where(Anomaly.device_id == device_id, Anomaly.detected_at >= since)
    )
    return (await session.execute(stmt)).scalar_one()


async def get_telemetry_page(
    session: AsyncSession,
    *,
    device_id: str | None,
    state: str | None,
    start: datetime | None,
    end: datetime | None,
    limit: int,
    offset: int,
) -> tuple[list[TelemetryEvent], int]:
    """Backend-paginated raw telemetry listing for the Telemetry Explorer —
    the full history is never sent to the browser in one response."""
    conditions = []
    if device_id:
        conditions.append(TelemetryEvent.device_id == device_id)
    if state:
        conditions.append(TelemetryEvent.state == state)
    if start:
        conditions.append(TelemetryEvent.time >= start)
    if end:
        conditions.append(TelemetryEvent.time <= end)

    count_stmt = select(func.count()).select_from(TelemetryEvent).where(*conditions)
    total = (await session.execute(count_stmt)).scalar_one()

    page_stmt = (
        select(TelemetryEvent)
        .where(*conditions)
        .order_by(TelemetryEvent.time.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(page_stmt)).scalars().all()
    return list(rows), total


async def get_power_trend(
    session: AsyncSession, start: datetime, end: datetime, bucket: str
) -> list[tuple[datetime, float | None]]:
    """Average observed power_watts per time bucket ('hour' or 'day') across
    the whole fleet, for the fleet-wide power trend chart."""
    bucket_expr = func.date_trunc(bucket, TelemetryEvent.time).label("bucket")
    stmt = (
        select(bucket_expr, func.avg(TelemetryEvent.power_watts))
        .where(
            TelemetryEvent.time >= start,
            TelemetryEvent.time <= end,
            TelemetryEvent.power_watts.is_not(None),
        )
        .group_by(bucket_expr)
        .order_by(bucket_expr)
    )
    rows = (await session.execute(stmt)).all()
    return [(row[0], row[1]) for row in rows]


async def list_fleet_anomalies(
    session: AsyncSession,
    *,
    device_id: str | None,
    anomaly_type: str | None,
    start: datetime | None,
    end: datetime | None,
    limit: int,
    offset: int,
) -> tuple[list[Anomaly], int]:
    conditions = []
    if device_id:
        conditions.append(Anomaly.device_id == device_id)
    if anomaly_type:
        conditions.append(Anomaly.anomaly_type == anomaly_type)
    if start:
        conditions.append(Anomaly.event_time >= start)
    if end:
        conditions.append(Anomaly.event_time <= end)

    count_stmt = select(func.count()).select_from(Anomaly).where(*conditions)
    total = (await session.execute(count_stmt)).scalar_one()

    page_stmt = (
        select(Anomaly)
        .where(*conditions)
        .order_by(Anomaly.event_time.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await session.execute(page_stmt)).scalars().all()
    return list(rows), total


async def get_telemetry_quality_counts(session: AsyncSession, since: datetime) -> dict:
    total_stmt = (
        select(func.count()).select_from(TelemetryEvent).where(TelemetryEvent.time >= since)
    )
    total = (await session.execute(total_stmt)).scalar_one()
    return {"accepted": total}


async def count_anomalies_by_type(session: AsyncSession, since: datetime) -> dict[str, int]:
    stmt = (
        select(Anomaly.anomaly_type, func.count())
        .where(Anomaly.detected_at >= since)
        .group_by(Anomaly.anomaly_type)
    )
    rows = (await session.execute(stmt)).all()
    return {row[0]: row[1] for row in rows}
