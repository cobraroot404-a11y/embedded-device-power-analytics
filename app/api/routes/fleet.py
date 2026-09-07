from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.periods import VALID_PERIODS
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.schemas.analytics import FleetSummary
from app.services.analytics_service import compute_fleet_summary

router = APIRouter(tags=["fleet"])


@router.get("/fleet/summary", response_model=FleetSummary)
async def fleet_summary(
    period: str | None = Query(default="daily"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> FleetSummary:
    if period is not None and period not in VALID_PERIODS:
        raise HTTPException(status_code=422, detail=f"period must be one of {sorted(VALID_PERIODS)}")
    if (start is None) != (end is None):
        raise HTTPException(status_code=422, detail="start and end must both be provided together")
    return await compute_fleet_summary(session, period, start, end, settings)
