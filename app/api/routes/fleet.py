from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.periods import VALID_PERIODS
from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.schemas.analytics import (
    FleetOverview,
    FleetPowerAnalytics,
    FleetStates,
    FleetSummary,
    FleetUsageTrend,
)
from app.services.analytics_service import (
    compute_fleet_summary,
    get_fleet_overview,
    get_fleet_power_analytics,
    get_fleet_states,
    get_fleet_usage_trend,
)

router = APIRouter(tags=["fleet"])


def _validate(period: str | None, start: datetime | None, end: datetime | None) -> None:
    if period is not None and period not in VALID_PERIODS:
        raise HTTPException(status_code=422, detail=f"period must be one of {sorted(VALID_PERIODS)}")
    if (start is None) != (end is None):
        raise HTTPException(status_code=422, detail="start and end must both be provided together")


@router.get("/fleet/summary", response_model=FleetSummary)
async def fleet_summary(
    period: str | None = Query(default="daily"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> FleetSummary:
    _validate(period, start, end)
    return await compute_fleet_summary(session, period, start, end, settings)


@router.get("/fleet/overview", response_model=FleetOverview)
async def fleet_overview(
    period: str | None = Query(default="daily"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> FleetOverview:
    _validate(period, start, end)
    return await get_fleet_overview(session, period, start, end, settings)


@router.get("/fleet/states", response_model=FleetStates)
async def fleet_states(session: AsyncSession = Depends(get_session)) -> FleetStates:
    return await get_fleet_states(session)


@router.get("/fleet/usage", response_model=FleetUsageTrend)
async def fleet_usage(
    period: str | None = Query(default="daily"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> FleetUsageTrend:
    _validate(period, start, end)
    return await get_fleet_usage_trend(session, period, start, end, settings)


@router.get("/fleet/power", response_model=FleetPowerAnalytics)
async def fleet_power(
    period: str | None = Query(default="daily"),
    start: datetime | None = Query(default=None),
    end: datetime | None = Query(default=None),
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> FleetPowerAnalytics:
    _validate(period, start, end)
    return await get_fleet_power_analytics(session, period, start, end, settings)
