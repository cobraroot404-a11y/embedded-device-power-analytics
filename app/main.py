from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import anomalies, devices, fleet, health, metrics, system, telemetry
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging(settings.log_level)

app = FastAPI(
    title="Embedded Device Usage & Power Analytics",
    description=(
        "Fleet-level usage, power-state, reliability and energy-efficiency "
        "analytics for embedded/IoT devices."
    ),
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_allow_origins.split(",") if o.strip()],
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(devices.router)
app.include_router(fleet.router)
app.include_router(anomalies.router)
app.include_router(telemetry.router)
app.include_router(system.router)
app.include_router(metrics.router)
