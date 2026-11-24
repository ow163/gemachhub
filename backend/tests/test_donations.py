"""בדיקות להצעת תרומה."""
from .conftest import FakeConn

VALID = {"donor_name": "משה כהן", "phone": "050-1234567", "item_name": "עגלת תינוק",
         "category_id": 3, "description": "במצב טוב", "point_id": 2}


class DonationConn(FakeConn):
    """חיבור מדומה: בבדיקת הנקודה והקטגוריה מחזיר ok, ובהכנסה מחזיר שורה חדשה."""

    def __init__(self, point_ok=True, category_ok=True):
        super().__init__()
        self.point_ok, self.category_ok = point_ok, category_ok

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        from .conftest import FakeResult
        if "point_ok" in sql:
            return FakeResult([{"point_ok": self.point_ok, "category_ok": self.category_ok}])
        return FakeResult([{"id": 7, "status": "pending", "created_at": "2026-11-22 10:00:00+00"}])


def test_create_donation_ok(make_client):
    conn = DonationConn()
    res = make_client(conn).post("/api/donations", json=VALID)
    assert res.status_code == 201
    assert res.get_json()["id"] == 7
    insert_params = conn.queries[-1][1]
    assert insert_params["phone"] == "0501234567"  # המקף הוסר
    assert insert_params["point_id"] == 2


def test_invalid_phone_rejected(make_client):
    conn = DonationConn()
    res = make_client(conn).post("/api/donations", json={**VALID, "phone": "12345"})
    assert res.status_code == 400
    assert "טלפון" in res.get_json()["error"]
    assert conn.queries == []  # לא הגענו לבסיס הנתונים


def test_missing_point_rejected(make_client):
    res = make_client(DonationConn()).post("/api/donations", json={**VALID, "point_id": ""})
    assert res.status_code == 400


def test_unknown_point_rejected(make_client):
    res = make_client(DonationConn(point_ok=False)).post("/api/donations", json=VALID)
    assert res.status_code == 400
    assert "נקודת המסירה" in res.get_json()["error"]


def test_recent_donations_limit_is_capped(make_client):
    conn = DonationConn()
    make_client(conn).get("/api/donations?limit=999")
    assert conn.queries[0][1] == {"limit": 20}
