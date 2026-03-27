from sqlalchemy.orm import Session
from typing import Optional
from app.models.signal import SignalPlan
from app.models.traffic import TrafficReading


# Base cycle times (seconds) per congestion band
SIGNAL_PROFILES = {
    "free":       {"green": 30, "red": 20, "cycle": 60},
    "moderate":   {"green": 45, "red": 25, "cycle": 80},
    "heavy":      {"green": 60, "red": 20, "cycle": 90},
    "standstill": {"green": 75, "red": 15, "cycle": 100},
}


def _label(level: float) -> str:
    if level < 0.25: return "free"
    if level < 0.5:  return "moderate"
    if level < 0.75: return "heavy"
    return "standstill"


def _build_phases(green: int, red: int, directions: int = 4) -> list:
    """Split green time across N directions."""
    per_dir = green // directions
    return [
        {"direction": f"D{i+1}", "green_s": per_dir, "red_s": red}
        for i in range(directions)
    ]


def optimize_signal(db: Session, junction_id: str, congestion_level: Optional[float] = None) -> dict:
    """
    Generate an optimized signal plan for a junction.
    Uses latest reading if congestion_level not provided.
    """
    if congestion_level is None:
        latest = db.query(TrafficReading).filter(
            TrafficReading.junction_id == junction_id
        ).order_by(TrafficReading.timestamp.desc()).first()

        if not latest:
            return {"error": "No traffic data for this junction"}

        # Simple congestion estimate from speed + density
        speed_score = max(0.0, 1.0 - (latest.speed_kmh / 80.0))
        density_score = min(latest.vehicle_density / 200.0, 1.0)
        congestion_level = round((speed_score * 0.5) + (density_score * 0.5), 3)

    label = _label(congestion_level)
    profile = SIGNAL_PROFILES[label]

    plan = SignalPlan(
        junction_id=junction_id,
        congestion_level=congestion_level,
        green_duration_s=profile["green"],
        red_duration_s=profile["red"],
        cycle_time_s=profile["cycle"],
        phases=_build_phases(profile["green"], profile["red"]),
        reason=_reason(label, congestion_level),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_to_dict(plan)


def _reason(label: str, level: float) -> str:
    reasons = {
        "free":       "Traffic is flowing freely. Standard timing applied.",
        "moderate":   "Moderate congestion detected. Green phase extended slightly.",
        "heavy":      "Heavy congestion. Green phase significantly extended to clear queues.",
        "standstill": "Near standstill. Maximum green time applied to reduce gridlock.",
    }
    return f"{reasons[label]} (congestion={level:.0%})"


def _plan_to_dict(plan: SignalPlan) -> dict:
    return {
        "junction_id": plan.junction_id,
        "congestion_level": plan.congestion_level,
        "green_duration_s": plan.green_duration_s,
        "red_duration_s": plan.red_duration_s,
        "cycle_time_s": plan.cycle_time_s,
        "phases": plan.phases,
        "reason": plan.reason,
        "generated_at": plan.generated_at,
    }
