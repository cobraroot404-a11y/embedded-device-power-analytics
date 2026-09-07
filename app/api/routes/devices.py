from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.periods import VALID_PERIODS
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.schemas.analytics import AnomalyOut, DeviceAnalytics, DeviceOut
from app.services import telemetry_repository as repo
from app.services.analytics_service import compute_device_analytics, is_device_active

router = APIRouter(tags=["devices"])


def _validate_period(period: str | None) -> None:
    if period is not None and period not in VALID_PERIODS:
        raise HTTPException(status_code=422, detail=f"period must be one of {sorted(VALID_PERIODS)}")


@router.get("/devices", response_model=list[DeviceOut])
async def list_devices(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> list[DeviceOut]:
    devices = await repo.list_devices(session)
    now = datetime.now(UTC)
    return [
        DeviceOut(
            device_id=d.device_id,
            first_seen=d.first_seen,
            last_seen=d.last_seen,
            last_state=d.last_state,
            last_boot_id=d.last_boot_id,
            is_active=is_device_active(d, settings, now),
        )
        for d in devices
    ]


@router.get("/devices/{device_id}", response_model=DeviceOut)
async def get_device(
    device_id: str,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> DeviceOut:
    device = await repo.get_device(session, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"device '{device_id}' not found")
    return DeviceOut(
        device_id=device.device_id,
        first_seen=device.first_seen,
        last_seen=device.last_seen,
        last_state=device.last_state,
        last_boot_id=device.last_boot_id,
        is_active=is_device_active(device, settings, datetime.now(UTC)),
    )


@router.get("/devices/{device_id}/summary", response_model=DeviceAnalytics)
async def device_summary(
    device_id: str,
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> DeviceAnalytics:
    device = await repo.get_device(session, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"device '{device_id}' not found")
    return await compute_device_analytics(session, device_id, "daily", None, None, settings)


@router.get("/devices/{device_id}/analytics", response_model=DeviceAnalytics)
async def device_analytics(
    device_id: str,
    period: str | None = Query(default="daily"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> DeviceAnalytics:
    _validate_period(period)
    device = await repo.get_device(session, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"device '{device_id}' not found")
    if (start is None) != (end is None):
        raise HTTPException(status_code=422, detail="start and end must both be provided together")
    return await compute_device_analytics(session, device_id, period, start, end, settings)


@router.get("/devices/{device_id}/anomalies", response_model=list[AnomalyOut])
async def device_anomalies(
    device_id: str,
    limit: int = Query(default=100, ge=1, le=1000),
    session: AsyncSession = Depends(get_session),
) -> list[AnomalyOut]:
    device = await repo.get_device(session, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail=f"device '{device_id}' not found")
    anomalies = await repo.list_anomalies(session, device_id, limit)
    return [
        AnomalyOut(
            id=str(a.id),
            device_id=a.device_id,
            anomaly_type=a.anomaly_type,
            detected_at=a.detected_at,
            event_time=a.event_time,
            details=a.details,
        )
        for a in anomalies
    ]
