"""נקודות הקצה הבסיסיות של ה-API: בדיקת חיבור, נקודות וקטגוריות.

כל קובץ בשם *_routes.py בתיקייה הזו נרשם אוטומטית (ראו create_app),
כך שכל חבר צוות מוסיף את הבקשות שלו בקובץ נפרד בלי להתנגש בקוד של אחרים.
"""
import logging

from flask import Blueprint, jsonify

from .db import get_conn

bp = Blueprint("core", __name__, url_prefix="/api")
log = logging.getLogger("gemachhub")


@bp.get("/health")
def health():
    """בדיקה שהשרת עובד ושיש חיבור לבסיס הנתונים."""
    try:
        get_conn().execute("select 1 as ok").fetchall()
    except Exception as exc:  # noqa: BLE001
        log.error("database check failed: %s", exc)
        return jsonify(status="error", database="disconnected"), 503
    return jsonify(status="ok", database="connected")


@bp.get("/points")
def list_points():
    """כל נקודות הגמ"ח הפעילות."""
    rows = get_conn().execute(
        """
        select id, name, neighborhood, address, opening_hours
        from points
        where is_active
        order by id
        """
    ).fetchall()
    return jsonify(rows)


@bp.get("/categories")
def list_categories():
    """קטגוריות הציוד לפי סדר התצוגה."""
    rows = get_conn().execute("select id, name from categories order by sort_order, id").fetchall()
    return jsonify(rows)
