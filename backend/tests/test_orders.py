"""בדיקות לעגלה (AB#109), ליצירת הזמנה (AB#114) ולמסך ההשאלות שלי (AB#151)."""
from datetime import date, timedelta

from .conftest import FakeConn, FakeResult


def next_weekday(weekday, after=1):
    """התאריך הקרוב (מחר והלאה) שנופל ביום weekday (שני=0 ... שבת=5, ראשון=6)."""
    d = date.today() + timedelta(days=after)
    while d.weekday() != weekday:
        d += timedelta(days=1)
    return d


SUNDAY = next_weekday(6)
ORDER = {"name": "יוסי כהן", "phone": "050-3333333", "point_id": 1, "start_date": SUNDAY.isoformat(),
         "end_date": (SUNDAY + timedelta(days=3)).isoformat(), "pickup_time": "17:30",
         "items": [{"item_id": 1, "qty": 2}]}


class OrderConn(FakeConn):
    def __init__(self, holidays=(), max_days=7, point=True, created=True, available=5):
        super().__init__()
        self.holidays, self.max_days, self.point, self.created, self.available = holidays, max_days, point, created, available

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        if "from holidays" in sql:
            return FakeResult([{"day": d, "name": "חג"} for d in self.holidays])
        if "min(max_loan_days)" in sql:
            return FakeResult([{"days": self.max_days}])
        if "from points where id" in sql:
            return FakeResult([{"name": "קריית יובל", "open_time": "17:00", "close_time": "20:00"}] if self.point else [])
        if "insert into orders" in sql:
            return FakeResult([{"id": 9, "code": params["code"], "deposit_total": 200, "units": 2}] if self.created else [])
        if "insert into notifications" in sql:
            return FakeResult([{"id": 1}])
        if "from items i where i.id" in sql:
            return FakeResult([{"name": "שולחן", "available_units": self.available}])
        return FakeResult([{"item_id": 1, "qty": 2, "name": "שולחן", "deposit_amount": 100, "max_loan_days": 7, "available_units": 3}])


def test_order_created(make_client):
    conn = OrderConn()
    res = make_client(conn).post("/api/orders", json=ORDER)
    assert res.status_code == 201
    assert res.get_json()["code"].startswith("GH-")
    params = next(p for q, p in conn.queries if "insert into orders" in q)
    assert params["item_ids"] == [1] and params["qtys"] == [2] and params["phone"] == "0503333333"
    assert any("insert into notifications" in q for q, _ in conn.queries)


def test_saturday_is_blocked(make_client):
    saturday = next_weekday(5)
    order = {**ORDER, "start_date": saturday.isoformat(), "end_date": (saturday + timedelta(days=1)).isoformat()}
    res = make_client(OrderConn()).post("/api/orders", json=order)
    assert res.status_code == 400
    assert "שבת" in res.get_json()["error"]


def test_holiday_is_blocked(make_client):
    res = make_client(OrderConn(holidays=[ORDER["end_date"]])).post("/api/orders", json=ORDER)
    assert res.status_code == 400
    assert "חג" in res.get_json()["error"]


def test_loan_longer_than_policy_is_blocked(make_client):
    res = make_client(OrderConn(max_days=2)).post("/api/orders", json=ORDER)
    assert res.status_code == 400
    assert "2 ימים" in res.get_json()["error"]


def test_pickup_outside_opening_hours(make_client):
    res = make_client(OrderConn()).post("/api/orders", json={**ORDER, "pickup_time": "21:00"})
    assert res.status_code == 400
    assert "שעות הפעילות" in res.get_json()["error"]


def test_past_date_rejected(make_client):
    past = (date.today() - timedelta(days=3)).isoformat()
    res = make_client(OrderConn()).post("/api/orders", json={**ORDER, "start_date": past})
    assert res.status_code == 400


def test_not_enough_units_returns_conflict(make_client):
    res = make_client(OrderConn(created=False)).post("/api/orders", json=ORDER)
    assert res.status_code == 409


def test_cart_total_deposit(make_client):
    res = make_client(OrderConn()).get("/api/cart?phone=050-3333333")
    body = res.get_json()
    assert body["deposit_total"] == 200 and body["count"] == 2


def test_cart_rejects_more_than_available(make_client):
    conn = OrderConn(available=1)
    res = make_client(conn).put("/api/cart", json={"phone": "0503333333", "item_id": 1, "qty": 3})
    assert res.status_code == 400
    assert "עד 1" in res.get_json()["error"]
    assert not any("insert into cart_items" in q for q, _ in conn.queries)


def test_cart_zero_removes_item(make_client):
    conn = OrderConn()
    make_client(conn).put("/api/cart", json={"phone": "0503333333", "item_id": 1, "qty": 0})
    assert any("delete from cart_items" in q for q, _ in conn.queries)


def test_my_loans_marks_overdue(make_client):
    rows = [{"id": 1, "code": "GH-1001", "status": "picked_up", "is_overdue": True, "days_late": 5, "items": []},
            {"id": 3, "code": "GH-1003", "status": "reserved", "is_overdue": False, "days_late": 0, "items": []}]
    res = make_client(FakeConn(rows)).get("/api/loans?phone=0501111111")
    body = res.get_json()
    assert body[0]["status_text"] == "באיחור"
    assert body[1]["status_text"] == "שוריינה, ממתינה לאיסוף"
