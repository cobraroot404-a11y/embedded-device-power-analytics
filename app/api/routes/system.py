from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.schemas.analytics import SystemHealth
from app.services.system_health import check_all_services

router = APIRouter(tags=["system"])


@router.get("/system/health", response_model=SystemHealth)
async def system_health(
    session: AsyncSession = Depends(get_session),
    settings: Settings = Depends(get_settings),
) -> SystemHealth:
    services = await check_all_services(session, settings)
    return SystemHealth(checked_at=datetime.now(UTC), services=services)
