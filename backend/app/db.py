"""חיבור לבסיס הנתונים (Supabase / PostgreSQL).

מחרוזת החיבור נקראת ממשתנה הסביבה DATABASE_URL שמגיע מקובץ .env.
כל בקשה מקבלת חיבור אחד מה-pool ומחזירה אותו בסוף הבקשה.
"""
import os

from flask import current_app, g

_pool = None


def _get_pool():
    global _pool
    if _pool is None:
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError("DATABASE_URL is not set - copy .env.example to .env and fill it in")
        # prepare_threshold=None נדרש עבור ה-pooler של Supabase (פורט 6543)
        _pool = ConnectionPool(
            conninfo=url,
            min_size=1,
            max_size=5,
            kwargs={"row_factory": dict_row, "prepare_threshold": None, "autocommit": True},
            open=True,
            timeout=10,
        )
    return _pool


def get_conn():
    """החיבור של הבקשה הנוכחית. בבדיקות אפשר להחליף אותו ב-DB_CONNECTION_FACTORY."""
    if "db_conn" not in g:
        factory = current_app.config.get("DB_CONNECTION_FACTORY")
        if factory:
            g.db_conn = factory()
        else:
            pool = _get_pool()
            g.db_pool = pool
            g.db_conn = pool.getconn()
    return g.db_conn


def close_conn(_exc=None):
    conn = g.pop("db_conn", None)
    pool = g.pop("db_pool", None)
    if conn is not None and pool is not None:
        pool.putconn(conn)
