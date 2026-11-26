"""מלאי הנקודה (AB#236): כל היחידות בנקודה לפי סטטוס, עם סינון לפי פריט (החלק של רפאל)."""
from flask import Blueprint, jsonify, request

from .db import get_conn

bp = Blueprint("inventory", __name__, url_prefix="/api")

STATUSES = ("available", "loaned", "repair", "lost")
STATUS_TEXT = {"available": "זמין", "loaned": "מושאל", "repair": "בתיקון", "lost": "אבד"}


@bp.get("/points/<int:point_id>/inventory")
def point_inventory(point_id):
    item_id = request.args.get("item_id", type=int)
    conn = get_conn()
    point = conn.execute("select id, name from points where id = %(id)s", {"id": point_id}).fetchone()
    if not point:
        return jsonify(error="הנקודה לא נמצאה"), 404
    units = conn.execute(
        """
        select u.id, u.code, u.status, i.id as item_id, i.name as item
        from units u
        join items i on i.id = u.item_id
        where u.point_id = %(point)s
          and (%(item)s::int is null or u.item_id = %(item)s::int)
        order by i.name, u.code
        """,
        {"point": point_id, "item": item_id},
    ).fetchall()
    summary = {s: 0 for s in STATUSES}
    for u in units:
        summary[u["status"]] = summary.get(u["status"], 0) + 1
        u["status_text"] = STATUS_TEXT.get(u["status"], u["status"])
    return jsonify(point=point, summary=summary, units=units)
