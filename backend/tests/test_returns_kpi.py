"""בדיקות לקליטת החזרה (AB#194), לתיעוד נזק (AB#204) וללוח הבקרה (AB#300)."""
from .test_point_admin import ScriptConn

PHOTO = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
ORDER = {"id": 2, "code": "GH-1002", "phone": "0502222222", "status": "picked_up", "point_id": 3,
         "open_codes": ["RM-STR-01", "RM-WCH-01"]}


def test_partial_return(make_client):
    conn = ScriptConn({"array_agg(u.code)": [ORDER],
                       "with target": [{"returned_now": 1, "remaining": 1, "order_status": None, "deposit_status": None}]})
    res = make_client(conn).post("/api/orders/2/return", json={"point_id": 3, "unit_codes": ["rm-str-01"]})
    assert res.status_code == 200
    assert res.get_json()["remaining"] == 1
    assert next(p for q, p in conn.queries if "with target" in q)["codes"] == ["RM-STR-01"]
    assert not any("insert into notifications" in q for q, _ in conn.queries)


def test_full_return_releases_deposit_and_notifies(make_client):
    conn = ScriptConn({"array_agg(u.code)": [ORDER],
                       "with target": [{"returned_now": 2, "remaining": 0, "order_status": "returned", "deposit_status": "released"}]})
    res = make_client(conn).post("/api/orders/2/return", json={"point_id": 3, "unit_codes": ["RM-STR-01", "RM-WCH-01"]})
    assert res.get_json()["deposit_status"] == "released"
    note = next(p for q, p in conn.queries if "insert into notifications" in q)
    assert "שוחררה" in note["message"]


def test_return_rejects_unknown_unit(make_client):
    res = make_client(ScriptConn({"array_agg(u.code)": [ORDER]})).post(
        "/api/orders/2/return", json={"point_id": 3, "unit_codes": ["KY-TBL-01"]})
    assert res.status_code == 400 and "KY-TBL-01" in res.get_json()["error"]


def test_return_other_point(make_client):
    res = make_client(ScriptConn({"array_agg(u.code)": [ORDER]})).post(
        "/api/orders/2/return", json={"point_id": 1, "unit_codes": ["RM-STR-01"]})
    assert res.status_code == 400


def test_damage_requires_photo_and_description(make_client):
    conn = ScriptConn({})
    res = make_client(conn).post("/api/units/RM-STR-01/damage", json={"severity": "medium", "description": "", "photo": ""})
    assert res.status_code == 400
    err = res.get_json()["error"]
    assert "תמונה" in err and "לתאר" in err
    assert conn.queries == []


def test_damage_severity_from_list(make_client):
    res = make_client(ScriptConn({})).post("/api/units/RM-STR-01/damage", json={"severity": "huge", "description": "שבר", "photo": PHOTO})
    assert res.status_code == 400


def test_damage_moves_unit_to_repair(make_client):
    conn = ScriptConn({"update units set status = 'repair'": [{"id": 4, "order_id": 2, "code": "RM-STR-01"}]})
    res = make_client(conn).post("/api/units/rm-str-01/damage", json={"severity": "medium", "description": "גלגל שבור", "photo": PHOTO})
    assert res.status_code == 201
    assert res.get_json()["unit_status"] == "repair" and res.get_json()["severity_text"] == "בינוני"


def test_kpi_uses_daily_snapshot(make_client):
    snap = {"day": "2026-11-26", "point_id": 1, "data": {"active_loans": 2}}
    conn = ScriptConn({"from kpi_daily where": [snap]})
    res = make_client(conn).get("/api/admin/kpi?point_id=1")
    assert res.get_json() == snap
    assert len(conn.queries) == 1  # כבר חושב היום, לא מחשבים שוב


def test_kpi_computed_once_a_day(make_client):
    conn = ScriptConn({"from kpi_daily where": [], "insert into kpi_daily": [{"day": "2026-11-26", "point_id": 0, "data": {}}]})
    make_client(conn).get("/api/admin/kpi")
    assert any("insert into kpi_daily" in q for q, _ in conn.queries)
