"""Standalone async MQTT telemetry consumer.

Runs as its own process (`python -m app.ingestion.consumer`), independent of
the FastAPI request lifecycle, per the architecture requirement that
ingestion must not share fate with the API server.
"""

import asyncio

import aiomqtt
from prometheus_client import start_http_server

from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.core.metrics import mqtt_processing_errors_total, telemetry_messages_received_total
from app.db.session import session_scope
from app.ingestion.pipeline import process_message

logger = get_logger(__name__)

RECONNECT_DELAY_SECONDS = 5


async def run_consumer() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    start_http_server(settings.consumer_metrics_port)
    logger.info(
        "consumer_starting",
        mqtt_host=settings.mqtt_host,
        mqtt_port=settings.mqtt_port,
        topic_filter=settings.mqtt_topic_filter,
        metrics_port=settings.consumer_metrics_port,
    )

    while True:
        try:
            async with aiomqtt.Client(hostname=settings.mqtt_host, port=settings.mqtt_port) as client:
                await client.subscribe(settings.mqtt_topic_filter)
                logger.info("consumer_connected", topic_filter=settings.mqtt_topic_filter)
                async for message in client.messages:
                    await _handle_message(settings, message)
        except aiomqtt.MqttError as exc:
            logger.warning("mqtt_connection_lost", error=str(exc), retry_in=RECONNECT_DELAY_SECONDS)
            await asyncio.sleep(RECONNECT_DELAY_SECONDS)


async def _handle_message(settings, message: aiomqtt.Message) -> None:
    telemetry_messages_received_total.inc()
    try:
        payload = message.payload
        if isinstance(payload, str):
            payload = payload.encode()
        async with session_scope() as session:
            await process_message(session, settings, payload, str(message.topic))
    except Exception:  # noqa: BLE001 - one bad message must never kill the consumer
        mqtt_processing_errors_total.inc()
        logger.exception("unexpected_processing_error", topic=str(message.topic))


def main() -> None:
    asyncio.run(run_consumer())


if __name__ == "__main__":
    main()
