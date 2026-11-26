"""בדיקות להצעת תרומה."""
from .conftest import FakeConn

PHOTO = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
VALID = {"donor_name": "משה כהן", "phone": "050-1234567", "item_name": "עגלת תינוק",
         "category_id": 3, "description": "במצב טוב", "point_id": 2, "photo": PHOTO}


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
        if "insert into notifications" in sql:
            return FakeResult([{"id": 1}])
        if "update donations" in sql:
            return FakeResult([{"id": 7, "phone": "0501234567", "item_name": "עגלת תינוק", "status": params["status"]}])
        return FakeResult([{"id": 7, "status": "pending", "created_at": "2026-11-22 10:00:00+00"}])


def test_create_donation_ok(make_client):
    conn = DonationConn()
    res = make_client(conn).post("/api/donations", json=VALID)
    assert res.status_code == 201
    assert res.get_json()["id"] == 7
    insert_params = next(p for q, p in conn.queries if "insert into donations" in q)
    assert insert_params["phone"] == "0501234567"  # המקף הוסר
    assert insert_params["point_id"] == 2
    assert insert_params["photo"] == PHOTO
    # AB#273: התורם מקבל הודעה עם מספר הפנייה
    note = next(p for q, p in conn.queries if "insert into notifications" in q)
    assert "7" in note["message"] and note["phone"] == "0501234567"


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


def test_photo_is_required(make_client):
    conn = DonationConn()
    res = make_client(conn).post("/api/donations", json={**VALID, "photo": ""})
    assert res.status_code == 400
    assert "תמונה" in res.get_json()["error"]
    assert conn.queries == []


def test_photo_must_be_an_image(make_client):
    res = make_client(DonationConn()).post("/api/donations", json={**VALID, "photo": "data:text/html;base64,PGI+"})
    assert res.status_code == 400


def test_my_donations_by_phone(make_client):
    rows = [{"id": 7, "item_name": "עגלת תינוק", "status": "approved", "point": "גילה", "created_at": "x"}]
    conn = FakeConn(rows)
    res = make_client(conn).get("/api/donations/mine?phone=050-1234567")
    assert res.status_code == 200
    assert res.get_json()[0]["status_text"] == "אושרה"
    assert conn.queries[0][1] == {"phone": "0501234567"}


def test_my_donations_rejects_bad_phone(make_client):
    res = make_client(FakeConn([])).get("/api/donations/mine?phone=123")
    assert res.status_code == 400


def test_status_change_notifies_donor(make_client):
    conn = DonationConn()
    res = make_client(conn).post("/api/donations/7/status", json={"status": "received"})
    assert res.status_code == 200
    assert res.get_json()["status_text"] == "נקלטה בנקודה"
    note = next(p for q, p in conn.queries if "insert into notifications" in q)
    assert "נקלטה בנקודה" in note["message"]


def test_status_change_rejects_unknown_status(make_client):
    res = make_client(DonationConn()).post("/api/donations/7/status", json={"status": "lost"})
    assert res.status_code == 400
