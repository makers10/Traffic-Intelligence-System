def test_signal_optimize_no_data(client):
    resp = client.post("/api/v1/signals/optimize", json={"junction_id": "EMPTY_J"})
    assert resp.status_code == 404


def test_signal_optimize_with_level(client):
    resp = client.post("/api/v1/signals/optimize", json={
        "junction_id": "J001",
        "congestion_level": 0.8,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["green_duration_s"] >= 60
    assert data["cycle_time_s"] > data["green_duration_s"]
    assert len(data["phases"]) == 4


def test_signal_optimize_free_flow(client):
    resp = client.post("/api/v1/signals/optimize", json={
        "junction_id": "J001",
        "congestion_level": 0.1,
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["green_duration_s"] == 30   # free flow profile
