from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_session
from app.schemas.analytics import TelemetryEventOut, TelemetryPage
from app.services import telemetry_repository as repo

router = APIRouter(tags=["telemetry"])


@router.get("/telemetry", response_model=TelemetryPage)
async def telemetry_explorer(
    device_id: str | None = Query(default=None),
    state: str | None = Query(default=None),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
) -> TelemetryPage:
    rows, total = await repo.get_telemetry_page(
        session, device_id=device_id, state=state, start=start, end=end, limit=limit, offset=offset
    )
    return TelemetryPage(
        items=[
            TelemetryEventOut(
                id=str(e.id),
                time=e.time,
                device_id=e.device_id,
                message_id=str(e.message_id),
                state=e.state,
                battery_percent=e.battery_percent,
                power_watts=e.power_watts,
                boot_id=e.boot_id,
                ingested_at=e.ingested_at,
            )
            for e in rows
        ],
        total=total,
        limit=limit,
        offset=offset,
    )
