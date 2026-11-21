"""בדיקות לנקודות הקצה הבסיסיות."""
from .conftest import FakeConn


def test_health_ok(make_client):
    res = make_client(FakeConn([{"ok": 1}])).get("/api/health")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok", "database": "connected"}


def test_health_db_down_returns_503(make_client):
    res = make_client(FakeConn(fail=True)).get("/api/health")
    assert res.status_code == 503
    assert res.get_json()["database"] == "disconnected"


def test_points_returns_rows(make_client):
    rows = [{"id": 1, "name": 'גמ"ח גילה', "neighborhood": "גילה", "address": "רחוב הגננת 5", "opening_hours": "א-ה"}]
    res = make_client(FakeConn(rows)).get("/api/points")
    assert res.status_code == 200
    assert res.get_json() == rows


def test_unknown_route_returns_json_404(make_client):
    res = make_client(FakeConn()).get("/api/nothing-here")
    assert res.status_code == 404
    assert "error" in res.get_json()
