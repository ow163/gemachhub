"""בדיקות לאיסופים להיום (AB#173), למסירה (AB#178) ולאישור תרומות (AB#279)."""
from .conftest import FakeConn, FakeResult

ORDER = {"id": 3, "code": "GH-1003", "borrower_name": "יוסי כהן", "phone": "0503333333", "status": "reserved",
         "point_id": 1, "point": "קריית יובל", "start_date": "2026-11-26", "end_date": "2026-11-29",
         "pickup_time": "18:00", "deposit_total": 110, "deposit_status": "held", "items": []}


class ScriptConn(FakeConn):
    """מחזיר תשובה לפי מילת מפתח בשאילתה."""

    def __init__(self, answers):
        super().__init__()
        self.answers = answers

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        for key, rows in self.answers.items():
            if key in sql:
                return FakeResult(rows(params) if callable(rows) else rows)
        return FakeResult([{"id": 1}])


def test_pickups_mark_collected(make_client):
    picked = {**ORDER, "status": "picked_up"}
    res = make_client(ScriptConn({"from orders o": [ORDER, picked]})).get("/api/points/1/pickups?date=2026-11-26")
    body = res.get_json()
    assert body["day"] == "2026-11-26"
    assert [p["collected"] for p in body["pickups"]] == [False, True]


def test_lookup_by_code_shows_valid_deposit(make_client):
    conn = ScriptConn({"from orders o": [ORDER]})
    res = make_client(conn).get("/api/orders/lookup?point_id=1&code=gh-1003")
    assert res.status_code == 200
    assert res.get_json()[0]["deposit_ok"] is True
    assert conn.queries[0][1] == {"code": "GH-1003"}


def test_lookup_order_of_other_point_is_error(make_client):
    res = make_client(ScriptConn({"from orders o": [ORDER]})).get("/api/orders/lookup?point_id=2&code=GH-1003")
    assert res.status_code == 400
    assert "נקודה אחרת" in res.get_json()["error"]


def test_lookup_by_phone(make_client):
    conn = ScriptConn({"from orders o": [ORDER]})
    res = make_client(conn).get("/api/orders/lookup?point_id=1&phone=050-3333333")
    assert res.status_code == 200
    assert conn.queries[0][1] == {"phone": "0503333333"}


def test_handover_marks_loaned_and_notifies(make_client):
    conn = ScriptConn({"update orders": [{"id": 3, "code": "GH-1003", "phone": "0503333333", "end_date": "2026-11-29", "units": 2}]})
    res = make_client(conn).post("/api/orders/3/handover", json={"point_id": 1})
    assert res.status_code == 200 and res.get_json()["units"] == 2
    assert any("insert into notifications" in q for q, _ in conn.queries)


def test_handover_rejected_when_not_possible(make_client):
    res = make_client(ScriptConn({"update orders": []})).post("/api/orders/3/handover", json={"point_id": 2})
    assert res.status_code == 409


def test_reject_requires_reason(make_client):
    conn = ScriptConn({})
    res = make_client(conn).post("/api/donations/5/decision", json={"decision": "reject", "reason": ""})
    assert res.status_code == 400
    assert conn.queries == []


def test_approve_notifies_and_writes_audit_log(make_client):
    conn = ScriptConn({
        "select status from donations": [{"status": "pending"}],
        "update donations set status": lambda p: [{"id": 5, "phone": "0527654321", "item_name": "לול", "status": p["status"]}],
    })
    res = make_client(conn).post("/api/donations/5/decision", json={"decision": "approve"})
    assert res.status_code == 200 and res.get_json()["status"] == "approved"
    sqls = " ".join(q for q, _ in conn.queries)
    assert "insert into notifications" in sqls and "insert into audit_log" in sqls


def test_decision_only_once(make_client):
    res = make_client(ScriptConn({"select status from donations": [{"status": "approved"}]})).post(
        "/api/donations/5/decision", json={"decision": "reject", "reason": "כפילות"})
    assert res.status_code == 409
