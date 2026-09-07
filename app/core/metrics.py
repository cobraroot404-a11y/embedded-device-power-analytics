"""Prometheus metric definitions shared by the API and telemetry-consumer processes.

Each process has its own process-local registry (prometheus_client default),
so the consumer exposes these on CONSUMER_METRICS_PORT while the API exposes
its own instance under /metrics. Labels are kept low-cardinality (no per-message
or per-device labels) to avoid metric explosion on fleets with many devices.
"""

from prometheus_client import Counter

telemetry_messages_received_total = Counter(
    "telemetry_messages_received_total",
    "Total MQTT telemetry messages received by the consumer",
)

telemetry_messages_valid_total = Counter(
    "telemetry_messages_valid_total",
    "Total telemetry messages that passed validation and were persisted",
)

telemetry_messages_rejected_total = Counter(
    "telemetry_messages_rejected_total",
    "Total telemetry messages rejected during validation",
    ["reason"],
)

telemetry_duplicates_total = Counter(
    "telemetry_duplicates_total",
    "Total telemetry messages identified as duplicates (same message_id)",
)

telemetry_out_of_order_total = Counter(
    "telemetry_out_of_order_total",
    "Total telemetry messages received with a device timestamp earlier than "
    "the device's already-persisted latest event",
)

device_communication_gaps_total = Counter(
    "device_communication_gaps_total",
    "Total communication gaps detected across all devices",
)

device_reboots_total = Counter(
    "device_reboots_total",
    "Total device reboot/session changes detected (boot_id change)",
)

mqtt_processing_errors_total = Counter(
    "mqtt_processing_errors_total",
    "Total unexpected errors while processing an MQTT message",
)
