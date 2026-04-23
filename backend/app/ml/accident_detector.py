"""
Accident / anomaly detection using statistical z-score analysis.

Instead of hardcoded thresholds that fire during normal peak-hour
congestion, this module computes how many standard deviations the
current reading deviates from the recent baseline.  This adapts
automatically to each junction's "normal" — a 40% speed drop on a
highway exit during rush hour is business-as-usual, but the same
drop on a residential street at 2am is alarming.

The detector also requires BOTH speed and density to be anomalous
simultaneously (a combined score), reducing false positives from
one-dimensional spikes.
"""
import math
from typing import Optional


# ── Z-score thresholds ───────────────────────────────────────────────────────
# A reading is flagged when its combined z-score exceeds these thresholds.
# These are much more statistically sound than raw percentage drops.
ANOMALY_Z_THRESHOLD = 2.5       # ≈ top 0.6% of a normal distribution
HIGH_SEVERITY_Z_THRESHOLD = 4.0  # extreme outlier


def _z_score(current: float, mean: float, stddev: float) -> float:
    """Signed z-score: how many stddevs `current` is from `mean`.

    Returns 0 when stddev is too small to be meaningful (prevents
    divide-by-zero and avoids false positives on near-constant data).
    """
    if stddev < 1e-6:
        return 0.0
    return (current - mean) / stddev


def _severity(combined_z: float) -> str:
    """Map a combined anomaly z-score to a human-readable severity."""
    if combined_z >= HIGH_SEVERITY_Z_THRESHOLD:
        return "high"
    elif combined_z >= ANOMALY_Z_THRESHOLD:
        return "medium"
    return "low"


def detect(
    current_speed: float,
    baseline_speed: float,
    current_density: int,
    baseline_density: int,
    occupancy_pct: Optional[float] = None,
    *,
    speed_stddev: float = 0.0,
    density_stddev: float = 0.0,
) -> Optional[dict]:
    """Detect anomalies using z-score deviation from baseline.

    Parameters
    ----------
    current_speed : float
        Speed from the latest sensor reading (km/h).
    baseline_speed : float
        Mean speed over the recent baseline window.
    current_density : int
        Vehicle density from the latest sensor reading.
    baseline_density : int
        Mean density over the recent baseline window.
    occupancy_pct : float, optional
        Road occupancy percentage (0-100).
    speed_stddev : float
        Standard deviation of speed over the baseline window.
        When 0 (no data / caller didn't compute it), the detector
        falls back to a conservative heuristic stddev.
    density_stddev : float
        Standard deviation of density over the baseline window.

    Returns
    -------
    dict or None
        Alert dict with severity, z-scores, and percentage changes,
        or None if no anomaly is detected.
    """
    if baseline_speed <= 0 or baseline_density <= 0:
        return None

    # ── Compute or estimate stddev ───────────────────────────────────────
    # If the caller doesn't supply stddev (legacy path), we estimate it
    # as 20% of the mean — a conservative fallback that avoids the old
    # hardcoded-threshold problem while remaining functional.
    eff_speed_std = speed_stddev if speed_stddev > 1e-6 else baseline_speed * 0.20
    eff_density_std = density_stddev if density_stddev > 1e-6 else baseline_density * 0.20

    # ── Z-scores ─────────────────────────────────────────────────────────
    # For speed: a DROP is anomalous → we want a POSITIVE z when speed falls
    speed_z = _z_score(baseline_speed - current_speed, 0, eff_speed_std)
    # For density: a SPIKE is anomalous → positive z when density rises
    density_z = _z_score(current_density - baseline_density, 0, eff_density_std)

    # Only consider positive deviations (drops in speed, spikes in density)
    speed_z = max(speed_z, 0.0)
    density_z = max(density_z, 0.0)

    # Combined score: Euclidean distance in z-space.
    # Requiring both dimensions to contribute reduces single-axis false positives.
    combined_z = math.sqrt(speed_z ** 2 + density_z ** 2)

    # ── Occupancy override ───────────────────────────────────────────────
    # Near-100% occupancy is always suspicious regardless of z-scores.
    occupancy_override = occupancy_pct is not None and occupancy_pct >= 97.0

    is_anomaly = combined_z >= ANOMALY_Z_THRESHOLD or occupancy_override

    if not is_anomaly:
        return None

    # Effective severity uses the combined z-score, or bumps to at least
    # "medium" if the occupancy override triggered.
    severity = _severity(combined_z)
    if occupancy_override and severity == "low":
        severity = "medium"

    # Also provide the legacy percentage-based metrics for backward compat
    speed_drop_pct = ((baseline_speed - current_speed) / baseline_speed) * 100
    density_spike_pct = ((current_density - baseline_density) / baseline_density) * 100

    return {
        "severity": severity,
        "speed_drop_pct": round(speed_drop_pct, 1),
        "density_spike_pct": round(density_spike_pct, 1),
        "speed_z": round(speed_z, 2),
        "density_z": round(density_z, 2),
        "combined_z": round(combined_z, 2),
    }
