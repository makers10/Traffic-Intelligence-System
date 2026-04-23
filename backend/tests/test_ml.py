from datetime import datetime
from app.ml.predictor import TrafficPredictor
from app.ml.accident_detector import detect


def test_heuristic_prediction_free():
    p = TrafficPredictor("TEST_J")
    result = p.predict(speed_kmh=70, vehicle_density=30, occupancy_pct=20,
                       weather_condition="clear", visibility_m=10000, horizon_minutes=30)
    assert result["label"] == "free"
    assert result["congestion_level"] < 0.25


def test_heuristic_prediction_heavy():
    p = TrafficPredictor("TEST_J")
    result = p.predict(speed_kmh=10, vehicle_density=180, occupancy_pct=90,
                       weather_condition="rain", visibility_m=3000, horizon_minutes=30)
    assert result["congestion_level"] > 0.5
    assert result["label"] in ["heavy", "standstill"]


def test_prediction_speed_decreases_with_congestion():
    p = TrafficPredictor("TEST_J")
    r1 = p.predict(speed_kmh=70, vehicle_density=30, occupancy_pct=20,
                   weather_condition="clear", visibility_m=10000)
    r2 = p.predict(speed_kmh=15, vehicle_density=190, occupancy_pct=95,
                   weather_condition="fog", visibility_m=500)
    assert r1["predicted_speed"] > r2["predicted_speed"]


# ── Accident detector (z-score based) ────────────────────────────────────────

def test_accident_no_anomaly():
    """Small deviations within normal variance should NOT trigger."""
    result = detect(
        current_speed=60, baseline_speed=65,
        current_density=100, baseline_density=95,
        speed_stddev=10.0, density_stddev=15.0,
    )
    assert result is None


def test_accident_speed_drop():
    """Extreme speed drop (many stddevs below baseline) should trigger."""
    result = detect(
        current_speed=10, baseline_speed=65,
        current_density=150, baseline_density=95,
        speed_stddev=8.0, density_stddev=10.0,
    )
    assert result is not None
    assert result["severity"] in ["medium", "high"]
    assert result["speed_drop_pct"] > 40
    assert "combined_z" in result  # new z-score field


def test_accident_density_spike():
    """Major density spike should trigger when combined with speed drop."""
    result = detect(
        current_speed=40, baseline_speed=62,
        current_density=200, baseline_density=80,
        speed_stddev=10.0, density_stddev=15.0,
    )
    assert result is not None
    assert result["density_spike_pct"] > 50


def test_accident_occupancy_trigger():
    """Near-100% occupancy should always trigger regardless of z-scores."""
    result = detect(
        current_speed=50, baseline_speed=55,
        current_density=100, baseline_density=98,
        occupancy_pct=97.0,
        speed_stddev=10.0, density_stddev=15.0,
    )
    assert result is not None


def test_accident_no_false_positive_during_peak():
    """A moderate slowdown with high variance (normal peak hour) should NOT trigger."""
    # 30% speed drop, but stddev is large (junction is naturally variable)
    result = detect(
        current_speed=45, baseline_speed=65,
        current_density=130, baseline_density=100,
        speed_stddev=20.0, density_stddev=25.0,
    )
    assert result is None, "Should not trigger during normal peak-hour variance"


def test_accident_backward_compat_no_stddev():
    """Detector should still work when stddev is not provided (legacy path)."""
    # Extreme deviation that should trigger even with estimated stddev
    result = detect(
        current_speed=5, baseline_speed=65,
        current_density=250, baseline_density=80,
    )
    assert result is not None
    assert result["severity"] in ["medium", "high"]
