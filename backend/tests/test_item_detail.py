"""בדיקות לכרטיס פריט מפורט (AB#103)."""
from .conftest import FakeConn

ITEM = {"id": 3, "name": "מיחם 100 כוסות", "description": "", "deposit_amount": 150, "max_loan_days": 7,
        "images": ["/img/cat-2.svg"], "category_id": 2, "category": "מטבח והגשה",
        "availability": [{"point_id": 1, "point": "קריית יובל", "available": 1}]}


def test_item_details(make_client):
    conn = FakeConn([ITEM])
    res = make_client(conn).get("/api/items/3")
    assert res.status_code == 200
    body = res.get_json()
    assert body["images"] and body["deposit_amount"] == 150 and body["max_loan_days"] == 7
    assert body["availability"][0]["available"] == 1
    assert conn.queries[0][1] == {"id": 3}


def test_item_not_found(make_client):
    res = make_client(FakeConn([])).get("/api/items/999")
    assert res.status_code == 404
