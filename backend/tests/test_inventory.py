"""בדיקות למלאי הנקודה (AB#236)."""
from .conftest import FakeConn, FakeResult


class InvConn(FakeConn):
    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        if "from points" in sql:
            return FakeResult([{"id": 1, "name": "קריית יובל"}] if params["id"] == 1 else [])
        return FakeResult([
            {"id": 1, "code": "KY-TBL-01", "status": "available", "item_id": 1, "item": "שולחן"},
            {"id": 2, "code": "KY-TBL-03", "status": "loaned", "item_id": 1, "item": "שולחן"},
            {"id": 3, "code": "KY-URN-02", "status": "repair", "item_id": 3, "item": "מיחם"},
        ])


def test_inventory_summary_by_status(make_client):
    res = make_client(InvConn()).get("/api/points/1/inventory")
    body = res.get_json()
    assert body["summary"] == {"available": 1, "loaned": 1, "repair": 1, "lost": 0}
    assert body["units"][2]["status_text"] == "בתיקון"


def test_inventory_filter_by_item(make_client):
    conn = InvConn()
    make_client(conn).get("/api/points/1/inventory?item_id=3")
    assert conn.queries[1][1] == {"point": 1, "item": 3}


def test_inventory_unknown_point(make_client):
    res = make_client(InvConn()).get("/api/points/9/inventory")
    assert res.status_code == 404
