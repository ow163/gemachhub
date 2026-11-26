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
    """כל נקודות הגמ"ח הפעילות, עם מיקום לתצוגה על המפה (AB#55). נקודה מושבתת לא מוצגת."""
    rows = get_conn().execute(
        """
        select id, name, neighborhood, address, opening_hours, lat, lng,
               to_char(open_time, 'HH24:MI') as open_time, to_char(close_time, 'HH24:MI') as close_time
        from points
        where is_active
        order by id
        """
    ).fetchall()
    return jsonify(rows)


@bp.get("/categories")
def list_categories():
    """קטגוריות הציוד לפי סדר התצוגה, עם מספר הפריטים בכל קטגוריה (AB#88)."""
    rows = get_conn().execute(
        """
        select c.id, c.name, count(i.id) as item_count
        from categories c
        left join items i on i.category_id = c.id
        group by c.id
        order by c.sort_order, c.id
        """
    ).fetchall()
    return jsonify(rows)
