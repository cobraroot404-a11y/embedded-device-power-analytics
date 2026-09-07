from fastapi import FastAPI

from app.api.routes import devices, fleet, health, metrics
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

app.include_router(health.router)
app.include_router(devices.router)
app.include_router(fleet.router)
app.include_router(metrics.router)
