"""Multi-device MQTT telemetry simulator.

Live mode (default):
    python -m simulator.run --devices 20 --interval 2

Publishes one telemetry message per device every `--interval` seconds, with
the device timestamp set to the current wall-clock time, indefinitely (or
for `--max-ticks` ticks if given, useful for scripted verification runs).

Backfill mode:
    python -m simulator.run --devices 20 --backfill-hours 72

Generates `--backfill-hours` of historical telemetry per device (5-minute
simulated ticks) and publishes it all immediately with historical
timestamps, so daily/weekly/monthly analytics have real data to compute over
without waiting for real time to pass.

`--seed` makes a run fully deterministic (same devices, same transitions,
same unreliable-delivery decisions) - used by integration tests.
"""

import argparse
import asyncio
import json
import random
import uuid
from datetime import UTC, datetime, timedelta

import aiomqtt

from simulator.devices import DeviceSimulator, build_fleet

BACKFILL_TICK_MINUTES = 5.0


class UnreliableDeliverySimulator:
    """Models duplicate, delayed/out-of-order, and dropped (gap-causing)
    delivery for devices with the "unreliable" profile. Decisions are driven
    by the shared per-device rng so a run is reproducible given --seed.

    A single dropped tick rarely spans the (default 30 minute) communication
    gap threshold on its own, so this also models occasional multi-tick
    "outages" — several consecutive ticks dropped in a row — which is what
    actually produces a real communication gap worth detecting."""

    DROP_PROBABILITY = 0.05
    DELAY_PROBABILITY = 0.10
    DUPLICATE_PROBABILITY = 0.05
    OUTAGE_START_PROBABILITY = 0.01
    OUTAGE_DURATION_TICKS = (8, 15)

    def __init__(self, rng: random.Random) -> None:
        self.rng = rng
        self.pending: list[tuple[int, dict]] = []
        self.recent_sent: list[dict] = []
        self.tick = 0
        self.outage_remaining = 0

    def offer(self, payload: dict) -> list[dict]:
        self.tick += 1

        if self.outage_remaining > 0:
            self.outage_remaining -= 1
            return []  # mid-outage: everything is silently dropped

        if self.rng.random() < self.OUTAGE_START_PROBABILITY:
            self.outage_remaining = self.rng.randint(*self.OUTAGE_DURATION_TICKS)
            return []

        to_publish: list[dict] = []
        roll = self.rng.random()
        if roll < self.DROP_PROBABILITY:
            pass  # single dropped message
        elif roll < self.DROP_PROBABILITY + self.DELAY_PROBABILITY:
            self.pending.append((self.tick + self.rng.randint(2, 4), payload))
        else:
            to_publish.append(payload)
            self.recent_sent.append(payload)

        ready = [p for t, p in self.pending if t <= self.tick]
        self.pending = [(t, p) for t, p in self.pending if t > self.tick]
        to_publish.extend(ready)

        if self.recent_sent and self.rng.random() < self.DUPLICATE_PROBABILITY:
            to_publish.append(self.rng.choice(self.recent_sent[-5:]))

        self.recent_sent = self.recent_sent[-20:]
        return to_publish


def _build_payload(device_id: str, timestamp: datetime, observed: dict) -> dict:
    return {
        "message_id": str(uuid.uuid4()),
        "device_id": device_id,
        "timestamp": timestamp.isoformat(),
        "state": observed["state"],
        "battery_percent": observed["battery_percent"],
        "power_watts": observed["power_watts"],
        "boot_id": observed["boot_id"],
    }


async def _publish(client: aiomqtt.Client, device_id: str, payload: dict) -> None:
    topic = f"devices/{device_id}/telemetry"
    await client.publish(topic, payload=json.dumps(payload).encode())


async def run_live(
    client: aiomqtt.Client,
    fleet: list[DeviceSimulator],
    interval: float,
    max_ticks: int | None,
    delivery: dict[str, UnreliableDeliverySimulator],
) -> int:
    tick_minutes = interval / 60.0
    published = 0
    tick = 0
    while max_ticks is None or tick < max_ticks:
        now = datetime.now(UTC)
        for device in fleet:
            observed = device.step(tick_minutes)
            payload = _build_payload(device.device_id, now, observed)
            outgoing = (
                delivery[device.device_id].offer(payload)
                if device.device_id in delivery
                else [payload]
            )
            for msg in outgoing:
                await _publish(client, device.device_id, msg)
                published += 1
        tick += 1
        await asyncio.sleep(interval)
    return published


async def run_backfill(
    client: aiomqtt.Client,
    fleet: list[DeviceSimulator],
    hours: float,
    delivery: dict[str, UnreliableDeliverySimulator],
) -> int:
    now = datetime.now(UTC)
    start = now - timedelta(hours=hours)
    ticks = int((hours * 60) / BACKFILL_TICK_MINUTES)
    published = 0

    for device in fleet:
        timestamp = start
        for _ in range(ticks):
            observed = device.step(BACKFILL_TICK_MINUTES)
            payload = _build_payload(device.device_id, timestamp, observed)
            outgoing = (
                delivery[device.device_id].offer(payload)
                if device.device_id in delivery
                else [payload]
            )
            for msg in outgoing:
                await _publish(client, device.device_id, msg)
                published += 1
            timestamp += timedelta(minutes=BACKFILL_TICK_MINUTES)

    return published


async def main_async(args: argparse.Namespace) -> None:
    fleet = build_fleet(args.devices, seed=args.seed)
    seed_source = random.Random(args.seed)
    delivery = {
        d.device_id: UnreliableDeliverySimulator(random.Random(seed_source.random()))
        for d in fleet
        if d.config.unreliable
    }

    print(f"Simulator starting: {len(fleet)} devices -> {args.mqtt_host}:{args.mqtt_port}")
    for d in fleet:
        print(f"  {d.device_id}: profile={d.profile}")

    async with aiomqtt.Client(hostname=args.mqtt_host, port=args.mqtt_port) as client:
        if args.backfill_hours > 0:
            count = await run_backfill(client, fleet, args.backfill_hours, delivery)
            print(f"Backfill complete: published {count} messages spanning {args.backfill_hours}h")
        else:
            count = await run_live(client, fleet, args.interval, args.max_ticks, delivery)
            print(f"Live run complete: published {count} messages")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Embedded device MQTT telemetry simulator")
    parser.add_argument("--devices", type=int, default=20)
    parser.add_argument("--interval", type=float, default=2.0, help="seconds between live ticks")
    parser.add_argument("--mqtt-host", type=str, default="localhost")
    parser.add_argument("--mqtt-port", type=int, default=1883)
    parser.add_argument("--seed", type=int, default=None, help="deterministic run when set")
    parser.add_argument(
        "--backfill-hours",
        type=float,
        default=0.0,
        help="generate this much historical data instead of live streaming",
    )
    parser.add_argument(
        "--max-ticks", type=int, default=None, help="stop after N live ticks (omit to run forever)"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    asyncio.run(main_async(args))


if __name__ == "__main__":
    main()
