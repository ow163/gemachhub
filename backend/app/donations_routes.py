"""הצעת תרומה - קליטת הצעות מתורמים (החלק של רפאל)."""
import re

from flask import Blueprint, jsonify, request

from .db import get_conn

bp = Blueprint("donations", __name__, url_prefix="/api")

PHONE_RE = re.compile(r"^05\d-?\d{7}$")


def _validate(data):
    """בדיקת שדות התרומה. מחזיר (נתונים נקיים, רשימת שגיאות)."""
    errors = []
    name = str(data.get("donor_name") or "").strip()
    phone = str(data.get("phone") or "").strip()
    item = str(data.get("item_name") or "").strip()
    desc = str(data.get("description") or "").strip()

    if not 2 <= len(name) <= 60:
        errors.append("שם התורם צריך להכיל 2 עד 60 תווים")
    if not PHONE_RE.match(phone):
        errors.append("מספר טלפון לא תקין (למשל 050-1234567)")
    if not 2 <= len(item) <= 80:
        errors.append("שם הפריט צריך להכיל 2 עד 80 תווים")
    if len(desc) > 500:
        errors.append("התיאור ארוך מדי (עד 500 תווים)")

    try:
        point_id = int(data.get("point_id"))
    except (TypeError, ValueError):
        point_id = None
        errors.append("יש לבחור נקודת מסירה")

    category_id = data.get("category_id")
    if category_id in ("", None):
        category_id = None
    else:
        try:
            category_id = int(category_id)
        except (TypeError, ValueError):
            category_id = None
            errors.append("קטגוריה לא תקינה")

    clean = {
        "donor_name": name,
        "phone": phone.replace("-", ""),
        "item_name": item,
        "description": desc,
        "point_id": point_id,
        "category_id": category_id,
    }
    return clean, errors


@bp.post("/donations")
def create_donation():
    """שמירת הצעת תרומה חדשה בסטטוס 'ממתינה'."""
    clean, errors = _validate(request.get_json(silent=True) or {})
    if errors:
        return jsonify(error=" · ".join(errors)), 400

    conn = get_conn()
    check = conn.execute(
        """
        select exists(select 1 from points where id = %(point_id)s and is_active) as point_ok,
               (%(category_id)s::int is null
                or exists(select 1 from categories where id = %(category_id)s::int)) as category_ok
        """,
        clean,
    ).fetchone()
    if not check["point_ok"]:
        return jsonify(error="נקודת המסירה לא נמצאה"), 400
    if not check["category_ok"]:
        return jsonify(error="הקטגוריה לא נמצאה"), 400

    row = conn.execute(
        """
        insert into donations (donor_name, phone, item_name, category_id, description, point_id)
        values (%(donor_name)s, %(phone)s, %(item_name)s, %(category_id)s, %(description)s, %(point_id)s)
        returning id, status, created_at::text as created_at
        """,
        clean,
    ).fetchone()
    return jsonify(row), 201


@bp.get("/donations")
def recent_donations():
    """רשימת ההצעות האחרונות (בלי שם וטלפון, לשמירה על פרטיות)."""
    limit = min(max(request.args.get("limit", default=5, type=int) or 5, 1), 20)
    rows = get_conn().execute(
        """
        select d.id, d.item_name, p.name as point, d.status, d.created_at::text as created_at
        from donations d
        join points p on p.id = d.point_id
        order by d.id desc
        limit %(limit)s
        """,
        {"limit": limit},
    ).fetchall()
    return jsonify(rows)
