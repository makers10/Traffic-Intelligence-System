from typing import Optional


SPEED_DROP_THRESHOLD = 0.40      # 40% sudden drop = anomaly
DENSITY_SPIKE_THRESHOLD = 0.50   # 50% sudden spike = anomaly


def _severity(speed_drop: float, density_spike: float) -> str:
    score = (speed_drop * 0.6) + (density_spike * 0.4)
    if score >= 0.7:
        return "high"
    elif score >= 0.4:
        return "medium"
    return "low"


def detect(
    current_speed: float,
    baseline_speed: float,
    current_density: int,
    baseline_density: int,
    occupancy_pct: Optional[float] = None,
) -> Optional[dict]:
    """
    Returns an alert dict if anomaly detected, else None.
    baseline_* = rolling average of last N readings for that junction.
    """
    if baseline_speed <= 0 or baseline_density <= 0:
        return None

    speed_drop = (baseline_speed - current_speed) / baseline_speed
    density_spike = (current_density - baseline_density) / baseline_density

    is_anomaly = (
        speed_drop >= SPEED_DROP_THRESHOLD or
        density_spike >= DENSITY_SPIKE_THRESHOLD or
        (occupancy_pct is not None and occupancy_pct >= 95.0)
    )

    if not is_anomaly:
        return None

    return {
        "severity": _severity(max(speed_drop, 0), max(density_spike, 0)),
        "speed_drop_pct": round(speed_drop * 100, 1),
        "density_spike_pct": round(density_spike * 100, 1),
    }
