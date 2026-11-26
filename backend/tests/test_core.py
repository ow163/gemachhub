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


def test_categories_include_item_count(make_client):
    rows = [{"id": 1, "name": "ריהוט לאירועים", "item_count": 2}]
    conn = FakeConn(rows)
    res = make_client(conn).get("/api/categories")
    assert res.get_json() == rows
    assert "count(i.id)" in conn.queries[0][0]


def test_points_return_location_and_only_active(make_client):
    rows = [{"id": 1, "name": "גמ\"ח קריית יובל", "lat": 31.76, "lng": 35.17, "open_time": "17:00", "close_time": "20:00"}]
    conn = FakeConn(rows)
    res = make_client(conn).get("/api/points")
    assert res.get_json()[0]["lat"] == 31.76
    assert "where is_active" in conn.queries[0][0]
