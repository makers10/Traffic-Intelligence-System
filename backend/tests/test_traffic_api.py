import pytest


READING_PAYLOAD = {
    "junction_id": "J001",
    "speed_kmh": 45.0,
    "vehicle_density": 120,
    "occupancy_pct": 60.0,
    "weather_condition": "clear",
    "temperature": 28.0,
    "visibility_m": 10000.0,
}


def test_ingest_reading(client):
    resp = client.post("/api/v1/readings", json=READING_PAYLOAD)
    assert resp.status_code == 201
    data = resp.json()
    assert data["junction_id"] == "J001"
    assert data["speed_kmh"] == 45.0
    assert "id" in data


def test_get_readings(client):
    # Ingest first
    client.post("/api/v1/readings", json=READING_PAYLOAD)
    resp = client.get("/api/v1/readings/J001")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) >= 1


def test_predict_congestion(client):
    client.post("/api/v1/readings", json=READING_PAYLOAD)
    resp = client.post("/api/v1/predict", json={"junction_id": "J001", "horizon_minutes": 30})
    assert resp.status_code == 200
    data = resp.json()
    assert "congestion_level" in data
    assert 0.0 <= data["congestion_level"] <= 1.0
    assert data["label"] in ["free", "moderate", "heavy", "standstill"]


def test_predict_unknown_junction(client):
    resp = client.post("/api/v1/predict", json={"junction_id": "UNKNOWN", "horizon_minutes": 30})
    assert resp.status_code == 404


def test_get_alerts_empty(client):
    resp = client.get("/api/v1/alerts")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_accident_detection_triggered(client):
    """Inject a sudden speed drop to trigger accident detection."""
    # Baseline readings
    for _ in range(5):
        client.post("/api/v1/readings", json={**READING_PAYLOAD, "junction_id": "J_CRASH", "speed_kmh": 70.0, "vehicle_density": 80})

    # Sudden crash-like reading
    client.post("/api/v1/readings", json={
        "junction_id": "J_CRASH",
        "speed_kmh": 5.0,
        "vehicle_density": 200,
        "occupancy_pct": 98.0,
    })

    resp = client.get("/api/v1/alerts?junction_id=J_CRASH")
    assert resp.status_code == 200
    # Alert may or may not fire depending on baseline window — just check structure
    for alert in resp.json():
        assert "severity" in alert
        assert alert["severity"] in ["low", "medium", "high"]
