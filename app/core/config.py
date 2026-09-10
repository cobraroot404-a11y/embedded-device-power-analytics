from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    database_url: str = (
        "postgresql+asyncpg://telemetry:telemetry_dev_password@localhost:5432/embedded_telemetry"
    )

    # MQTT
    mqtt_host: str = "localhost"
    mqtt_port: int = 1883
    mqtt_topic_filter: str = "devices/+/telemetry"
    mqtt_client_id_prefix: str = "telemetry-consumer"

    # Analytics thresholds (centralised, no magic numbers scattered in code)
    gap_threshold_minutes: int = 30
    rarely_used_on_percent: float = 10.0
    excessive_on_hours: float = 8.0
    poor_power_saving_percent: float = 20.0
    low_battery_percent: float = 20.0
    abnormal_power_multiplier: float = 2.5

    # Consumer metrics HTTP server (separate process from the API)
    consumer_host: str = "localhost"
    consumer_metrics_port: int = 9100

    # Other observability/frontend services, checked by GET /system/health
    prometheus_url: str = "http://localhost:9090"
    grafana_url: str = "http://localhost:3000"
    frontend_health_url: str = "http://localhost:3000"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    log_level: str = "INFO"
    cors_allow_origins: str = "http://localhost:3000"

    @property
    def gap_threshold_seconds(self) -> float:
        return self.gap_threshold_minutes * 60


@lru_cache
def get_settings() -> Settings:
    return Settings()
