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


def test_accident_no_anomaly():
    result = detect(current_speed=60, baseline_speed=65, current_density=100, baseline_density=95)
    assert result is None


def test_accident_speed_drop():
    result = detect(current_speed=10, baseline_speed=65, current_density=100, baseline_density=95)
    assert result is not None
    assert result["severity"] in ["medium", "high"]
    assert result["speed_drop_pct"] > 40


def test_accident_density_spike():
    result = detect(current_speed=60, baseline_speed=62, current_density=200, baseline_density=80)
    assert result is not None
    assert result["density_spike_pct"] > 50


def test_accident_occupancy_trigger():
    result = detect(current_speed=50, baseline_speed=55, current_density=100,
                    baseline_density=98, occupancy_pct=97.0)
    assert result is not None
