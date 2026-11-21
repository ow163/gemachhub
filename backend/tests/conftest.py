"""כלים משותפים לבדיקות: חיבור מדומה לבסיס הנתונים."""
import pytest

from app import create_app


class FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def fetchall(self):
        return self._rows

    def fetchone(self):
        return self._rows[0] if self._rows else None


class FakeConn:
    """מחזיר תשובה קבועה לכל שאילתה, ושומר את השאילתות שהורצו."""

    def __init__(self, rows=None, fail=False):
        self.rows = rows if rows is not None else []
        self.fail = fail
        self.queries = []

    def execute(self, sql, params=None):
        if self.fail:
            raise RuntimeError("db down")
        self.queries.append((sql, params))
        return FakeResult(self.rows)


@pytest.fixture
def make_client():
    def _make(conn):
        app = create_app({"TESTING": True, "DB_CONNECTION_FACTORY": lambda: conn})
        return app.test_client()

    return _make
