"""Energy estimation from state durations and observed power_watts samples.

Energy is only estimated for states where at least one power_watts sample was
observed — we never fabricate a power figure for a state that reported none.
battery_percent is a device-reported charge level, not an energy measurement,
and is never used as a substitute for power_watts here.
"""

from dataclasses import dataclass

from app.analytics.state_duration import DurationResult


@dataclass(slots=True)
class EnergyEstimate:
    on_avg_power_watts: float | None
    sleep_avg_power_watts: float | None
    off_avg_power_watts: float | None
    estimated_energy_kwh: float | None
    is_estimated: bool = True


def _avg(samples: list[float]) -> float | None:
    return sum(samples) / len(samples) if samples else None


def estimate_energy(result: DurationResult) -> EnergyEstimate:
    on_avg = _avg(result.on_power_samples)
    sleep_avg = _avg(result.sleep_power_samples)
    off_avg = _avg(result.off_power_samples)

    energy_kwh = 0.0
    have_any = False

    for avg_power, seconds in (
        (on_avg, result.on_seconds),
        (sleep_avg, result.sleep_seconds),
        (off_avg, result.off_seconds),
    ):
        if avg_power is None:
            continue
        have_any = True
        hours = seconds / 3600.0
        energy_kwh += (avg_power * hours) / 1000.0

    return EnergyEstimate(
        on_avg_power_watts=on_avg,
        sleep_avg_power_watts=sleep_avg,
        off_avg_power_watts=off_avg,
        estimated_energy_kwh=energy_kwh if have_any else None,
    )
