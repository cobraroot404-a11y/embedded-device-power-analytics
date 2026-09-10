"""Real reachability checks for every service in the stack.

Each check either succeeds, fails, or times out — there is no fabricated
"assume healthy" fallback. A service this process genuinely cannot reach or
does not know how to probe is reported as unknown, never as healthy.
"""

import asyncio
import contextlib

import httpx
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.schemas.analytics import ServiceStatus

HEALTHY = "healthy"
DEGRADED = "degraded"
UNAVAILABLE = "unavailable"
UNKNOWN = "unknown"


async def _check_tcp(host: str, port: int, connect_timeout: float = 2.0) -> ServiceStatus:
    name = f"{host}:{port}"
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=connect_timeout
        )
        writer.close()
        with contextlib.suppress(Exception):
            await writer.wait_closed()
        return ServiceStatus(name=name, status=HEALTHY)
    except (TimeoutError, OSError) as exc:
        return ServiceStatus(name=name, status=UNAVAILABLE, detail=str(exc))


async def _check_http(url: str, client: httpx.AsyncClient) -> tuple[str, str | None]:
    try:
        resp = await client.get(url, timeout=2.0)
        if resp.status_code < 500:
            return HEALTHY, None
        return DEGRADED, f"HTTP {resp.status_code}"
    except httpx.HTTPError as exc:
        return UNAVAILABLE, str(exc)


async def check_database(session: AsyncSession) -> ServiceStatus:
    try:
        await session.execute(text("SELECT 1"))
        return ServiceStatus(name="timescaledb", status=HEALTHY)
    except SQLAlchemyError as exc:
        return ServiceStatus(name="timescaledb", status=UNAVAILABLE, detail=str(exc))


async def check_all_services(session: AsyncSession, settings: Settings) -> list[ServiceStatus]:
    db_check = check_database(session)
    mqtt_check = _check_tcp(settings.mqtt_host, settings.mqtt_port)
    consumer_check = _check_tcp(settings.consumer_host, settings.consumer_metrics_port)

    async with httpx.AsyncClient() as client:
        prometheus_status, prometheus_detail = await _check_http(
            f"{settings.prometheus_url}/-/healthy", client
        )
        grafana_status, grafana_detail = await _check_http(
            f"{settings.grafana_url}/api/health", client
        )
        frontend_status, frontend_detail = await _check_http(settings.frontend_health_url, client)

    db_result, mqtt_result, consumer_result = await asyncio.gather(
        db_check, mqtt_check, consumer_check
    )

    return [
        ServiceStatus(name="fastapi", status=HEALTHY),
        ServiceStatus(name="mqtt_broker", status=mqtt_result.status, detail=mqtt_result.detail),
        ServiceStatus(
            name="telemetry_consumer", status=consumer_result.status, detail=consumer_result.detail
        ),
        db_result,
        ServiceStatus(name="prometheus", status=prometheus_status, detail=prometheus_detail),
        ServiceStatus(name="grafana", status=grafana_status, detail=grafana_detail),
        ServiceStatus(name="frontend", status=frontend_status, detail=frontend_detail),
    ]
