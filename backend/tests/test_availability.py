"""בדיקות לזמינות בטווח תאריכים (AB#98) ולרשימת האיחורים (AB#215)."""
from .conftest import FakeConn

ROWS = [{"id": 1, "name": "שולחן", "available_units": 0, "next_free_date": "2026-12-03"},
        {"id": 2, "name": "כיסא", "available_units": 2, "next_free_date": "2026-12-01"}]


def test_range_uses_overlap_query(make_client):
    conn = FakeConn([dict(r) for r in ROWS])
    res = make_client(conn).get("/api/items?start=2026-12-01&end=2026-12-03&point=1")
    assert res.status_code == 200
    sql, params = conn.queries[0]
    assert "order_units" in sql and params["start"] == "2026-12-01" and params["point"] == 1
    body = res.get_json()
    assert body[0]["next_free_date"] == "2026-12-03"   # לא זמין: מוצג מתי יתפנה
    assert body[1]["next_free_date"] is None            # זמין: אין צורך בתאריך


def test_range_requires_both_dates(make_client):
    res = make_client(FakeConn([])).get("/api/items?start=2026-12-01")
    assert res.status_code == 400


def test_range_end_before_start(make_client):
    res = make_client(FakeConn([])).get("/api/items?start=2026-12-05&end=2026-12-01")
    assert res.status_code == 400


def test_overdue_sorted_by_days_late(make_client):
    rows = [{"code": "GH-1001", "days_late": 5, "phone": "0501111111", "items": [{"item": "שולחן", "qty": 1}]}]
    conn = FakeConn(rows)
    res = make_client(conn).get("/api/points/1/overdue")
    assert res.get_json() == rows
    sql, params = conn.queries[0]
    assert "order by days_late desc" in sql and params == {"point": 1}
