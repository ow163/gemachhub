"""בדיקות לקטלוג הפריטים."""
from .conftest import FakeConn

ROWS = [{"id": 3, "name": "מיחם 100 כוסות", "description": "", "deposit_amount": 150, "max_loan_days": 7,
         "category_id": 2, "category": "מטבח והגשה", "available_units": 2}]


def test_items_returns_catalog(make_client):
    conn = FakeConn(ROWS)
    res = make_client(conn).get("/api/items")
    assert res.status_code == 200
    assert res.get_json() == ROWS
    _, params = conn.queries[0]
    assert params == {"category": None, "q": None}


def test_items_passes_filters(make_client):
    conn = FakeConn(ROWS)
    make_client(conn).get("/api/items?category=2&q=%20מיחם%20")
    _, params = conn.queries[0]
    assert params == {"category": 2, "q": "מיחם"}


def test_items_ignores_invalid_category(make_client):
    conn = FakeConn([])
    res = make_client(conn).get("/api/items?category=abc")
    assert res.status_code == 200
    assert conn.queries[0][1]["category"] is None


def test_search_ignores_niqqud_and_extra_spaces(make_client):
    conn = FakeConn([])
    make_client(conn).get("/api/items?q=" + "  מֵיחַם   גָּדוֹל ")
    assert conn.queries[0][1]["q"] == "מיחם גדול"


def test_empty_search_after_cleanup_is_none():
    from app.items_routes import normalize_query
    assert normalize_query("   ") is None
    assert normalize_query("כִּסֵּא") == "כסא"
