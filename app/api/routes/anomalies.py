from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.severity import get_severity
from app.db.session import get_session
from app.schemas.analytics import AnomalyOut, AnomalySummary, PagedAnomalies
from app.services import telemetry_repository as repo
from app.services.analytics_service import get_anomaly_summary

router = APIRouter(tags=["anomalies"])


@router.get("/anomalies", response_model=PagedAnomalies)
async def list_anomalies(
    device_id: str | None = Query(default=None),
    anomaly_type: str | None = Query(default=None),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> PagedAnomalies:
    rows, total = await repo.list_fleet_anomalies(
        session,
        device_id=device_id,
        anomaly_type=anomaly_type,
        start=start,
        end=end,
        limit=limit,
        offset=offset,
    )
    return PagedAnomalies(
        items=[
            AnomalyOut(
                id=str(a.id),
                device_id=a.device_id,
                anomaly_type=a.anomaly_type,
                severity=get_severity(a.anomaly_type, a.details),
                detected_at=a.detected_at,
                event_time=a.event_time,
                details=a.details,
            )
            for a in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/anomalies/summary", response_model=AnomalySummary)
async def anomaly_summary(
    hours: int = Query(default=24, ge=1, le=24 * 30),
    session: AsyncSession = Depends(get_session),
) -> AnomalySummary:
    since = datetime.now(UTC) - timedelta(hours=hours)
    return await get_anomaly_summary(session, since)
