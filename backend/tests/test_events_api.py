from datetime import datetime, timedelta


def _event_payload(junction_id="J001", attendance=10000):
    return {
        "name": "Test Concert",
        "event_type": "concert",
        "junction_id": junction_id,
        "location": "City Arena",
        "starts_at": (datetime.utcnow() + timedelta(hours=1)).isoformat(),
        "ends_at": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
        "expected_attendance": attendance,
        "impact_radius_km": 2.0,
        "source": "manual",
    }


def test_create_event(client):
    resp = client.post("/api/v1/events", json=_event_payload())
    assert resp.status_code == 201
    data = resp.json()
    assert data["impact_score"] > 0
    assert data["event_type"] == "concert"


def test_high_attendance_high_impact(client):
    resp = client.post("/api/v1/events", json=_event_payload(attendance=50000))
    assert resp.status_code == 201
    assert resp.json()["impact_score"] >= 0.8


def test_low_attendance_low_impact(client):
    resp = client.post("/api/v1/events", json=_event_payload(attendance=200))
    assert resp.status_code == 201
    assert resp.json()["impact_score"] < 0.4


def test_list_active_events(client):
    client.post("/api/v1/events", json=_event_payload())
    resp = client.get("/api/v1/events")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
