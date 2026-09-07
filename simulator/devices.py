"""Device profile state machines.

Each profile is a small weighted state machine over ON/SLEEP/OFF with a
"dwell" (how many ticks to remain in the current state) drawn from a
profile-specific range. A "tick" is deliberately abstract: in live mode a
tick is one publish interval (seconds); in backfill mode a tick is a fixed
slice of simulated wall-clock time (minutes) so a short-lived simulator run
can still produce statistically meaningful daily/weekly/monthly history.

`unreliable` is a flag consulted by the publisher (simulator/run.py), not by
this module — duplication/delay/reordering/dropped-gap behaviour is a
property of *delivery*, not of the device's own state.
"""

import random
import uuid
from dataclasses import dataclass, field
from typing import Any

ON, SLEEP, OFF = "ON", "SLEEP", "OFF"


@dataclass(frozen=True)
class ProfileConfig:
    dwell_ticks: dict[str, tuple[int, int]]
    transitions: dict[str, dict[str, float]]
    power_baseline: dict[str, float]
    battery_decline_per_hour: float
    reboot_probability: float
    power_spike_probability: float
    power_spike_multiplier: float
    initial_battery: float
    unreliable: bool = False


PROFILES: dict[str, ProfileConfig] = {
    "normal": ProfileConfig(
        dwell_ticks={ON: (8, 20), SLEEP: (4, 10), OFF: (2, 8)},
        transitions={
            ON: {SLEEP: 0.7, OFF: 0.3},
            SLEEP: {ON: 0.7, OFF: 0.3},
            OFF: {ON: 0.8, SLEEP: 0.2},
        },
        power_baseline={ON: 5.0, SLEEP: 0.8, OFF: 0.0},
        battery_decline_per_hour=0.5,
        reboot_probability=0.0005,
        power_spike_probability=0.0,
        power_spike_multiplier=1.0,
        initial_battery=95.0,
    ),
    "efficient": ProfileConfig(
        dwell_ticks={ON: (3, 8), SLEEP: (10, 25), OFF: (3, 10)},
        transitions={
            ON: {SLEEP: 0.9, OFF: 0.1},
            SLEEP: {ON: 0.5, OFF: 0.5},
            OFF: {ON: 0.6, SLEEP: 0.4},
        },
        power_baseline={ON: 4.5, SLEEP: 0.3, OFF: 0.0},
        battery_decline_per_hour=0.3,
        reboot_probability=0.0005,
        power_spike_probability=0.0,
        power_spike_multiplier=1.0,
        initial_battery=95.0,
    ),
    "underutilised": ProfileConfig(
        dwell_ticks={ON: (2, 5), SLEEP: (5, 12), OFF: (20, 50)},
        transitions={
            ON: {OFF: 0.8, SLEEP: 0.2},
            SLEEP: {OFF: 0.8, ON: 0.2},
            OFF: {ON: 0.5, SLEEP: 0.5},
        },
        power_baseline={ON: 5.0, SLEEP: 0.5, OFF: 0.0},
        battery_decline_per_hour=0.2,
        reboot_probability=0.0003,
        power_spike_probability=0.0,
        power_spike_multiplier=1.0,
        initial_battery=90.0,
    ),
    "inefficient": ProfileConfig(
        dwell_ticks={ON: (40, 80), SLEEP: (2, 5), OFF: (1, 3)},
        transitions={
            ON: {SLEEP: 0.7, OFF: 0.3},
            SLEEP: {ON: 0.9, OFF: 0.1},
            OFF: {ON: 0.95, SLEEP: 0.05},
        },
        power_baseline={ON: 6.5, SLEEP: 1.0, OFF: 0.0},
        battery_decline_per_hour=0.8,
        reboot_probability=0.0002,
        power_spike_probability=0.0,
        power_spike_multiplier=1.0,
        initial_battery=95.0,
    ),
    "unreliable": ProfileConfig(
        dwell_ticks={ON: (8, 20), SLEEP: (4, 10), OFF: (2, 8)},
        transitions={
            ON: {SLEEP: 0.7, OFF: 0.3},
            SLEEP: {ON: 0.7, OFF: 0.3},
            OFF: {ON: 0.8, SLEEP: 0.2},
        },
        power_baseline={ON: 5.0, SLEEP: 0.8, OFF: 0.0},
        battery_decline_per_hour=0.5,
        reboot_probability=0.0005,
        power_spike_probability=0.0,
        power_spike_multiplier=1.0,
        initial_battery=95.0,
        unreliable=True,
    ),
    "rebooting": ProfileConfig(
        dwell_ticks={ON: (8, 20), SLEEP: (4, 10), OFF: (2, 8)},
        transitions={
            ON: {SLEEP: 0.7, OFF: 0.3},
            SLEEP: {ON: 0.7, OFF: 0.3},
            OFF: {ON: 0.8, SLEEP: 0.2},
        },
        power_baseline={ON: 5.0, SLEEP: 0.8, OFF: 0.0},
        battery_decline_per_hour=0.5,
        reboot_probability=0.03,
        power_spike_probability=0.0,
        power_spike_multiplier=1.0,
        initial_battery=95.0,
    ),
    "low_battery": ProfileConfig(
        dwell_ticks={ON: (8, 20), SLEEP: (4, 10), OFF: (2, 8)},
        transitions={
            ON: {SLEEP: 0.7, OFF: 0.3},
            SLEEP: {ON: 0.7, OFF: 0.3},
            OFF: {ON: 0.8, SLEEP: 0.2},
        },
        power_baseline={ON: 5.0, SLEEP: 0.8, OFF: 0.0},
        battery_decline_per_hour=6.0,
        reboot_probability=0.0005,
        power_spike_probability=0.0,
        power_spike_multiplier=1.0,
        initial_battery=35.0,
    ),
    "abnormal_power": ProfileConfig(
        dwell_ticks={ON: (8, 20), SLEEP: (4, 10), OFF: (2, 8)},
        transitions={
            ON: {SLEEP: 0.7, OFF: 0.3},
            SLEEP: {ON: 0.7, OFF: 0.3},
            OFF: {ON: 0.8, SLEEP: 0.2},
        },
        power_baseline={ON: 5.0, SLEEP: 0.8, OFF: 0.0},
        battery_decline_per_hour=0.5,
        reboot_probability=0.0005,
        power_spike_probability=0.08,
        power_spike_multiplier=4.0,
        initial_battery=95.0,
    ),
}

PROFILE_NAMES = list(PROFILES.keys())


@dataclass
class DeviceSimulator:
    device_id: str
    profile: str
    rng: random.Random
    state: str = ON
    dwell_remaining: int = field(default=0)
    battery: float = 100.0
    boot_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def __post_init__(self) -> None:
        cfg = PROFILES[self.profile]
        self.battery = cfg.initial_battery
        self.dwell_remaining = self._roll_dwell(self.state)

    @property
    def config(self) -> ProfileConfig:
        return PROFILES[self.profile]

    def _roll_dwell(self, state: str) -> int:
        lo, hi = self.config.dwell_ticks[state]
        return self.rng.randint(lo, hi)

    def _next_state(self) -> str:
        weights = self.config.transitions[self.state]
        states = list(weights.keys())
        probs = list(weights.values())
        return self.rng.choices(states, weights=probs, k=1)[0]

    def step(self, tick_minutes: float) -> dict[str, Any]:
        """Advances the state machine by one tick and returns the telemetry
        fields (state/battery/power/boot_id) observed *during* this tick,
        before the transition takes effect for the next one."""
        cfg = self.config

        decline = cfg.battery_decline_per_hour * (tick_minutes / 60.0)
        self.battery = max(0.0, round(self.battery - decline, 2))

        if self.rng.random() < cfg.reboot_probability:
            self.boot_id = str(uuid.uuid4())

        baseline = cfg.power_baseline[self.state]
        power = baseline * self.rng.uniform(0.85, 1.15)
        if self.rng.random() < cfg.power_spike_probability:
            power *= cfg.power_spike_multiplier

        observed = {
            "state": self.state,
            "battery_percent": round(self.battery, 1),
            "power_watts": round(power, 2),
            "boot_id": self.boot_id,
        }

        self.dwell_remaining -= 1
        if self.dwell_remaining <= 0:
            self.state = self._next_state()
            self.dwell_remaining = self._roll_dwell(self.state)

        return observed


def build_fleet(num_devices: int, seed: int | None = None) -> list[DeviceSimulator]:
    rng = random.Random(seed)
    devices = []
    for i in range(1, num_devices + 1):
        profile = PROFILE_NAMES[(i - 1) % len(PROFILE_NAMES)]
        device_id = f"MIF-{i:03d}"
        devices.append(DeviceSimulator(device_id=device_id, profile=profile, rng=random.Random(rng.random())))
    return devices
