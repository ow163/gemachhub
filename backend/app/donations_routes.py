"""הצעת תרומה - קליטת הצעות מתורמים ומעקב אחרי הסטטוס (החלק של רפאל)."""
import re

from flask import Blueprint, jsonify, request

from .db import get_conn
from .notify import notify

bp = Blueprint("donations", __name__, url_prefix="/api")

PHONE_RE = re.compile(r"^05\d-?\d{7}$")
PHOTO_RE = re.compile(r"^data:image/(png|jpe?g|webp|gif);base64,[A-Za-z0-9+/=]+$")
MAX_PHOTO_CHARS = 3_000_000  # בערך 2MB של תמונה

STATUS_TEXT = {
    "pending": "ממתינה לאישור",
    "approved": "אושרה",
    "rejected": "נדחתה",
    "received": "נקלטה בנקודה",
}


def normalize_phone(phone):
    phone = str(phone or "").strip()
    return phone.replace("-", "") if PHONE_RE.match(phone) else None


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

    # AB#258: חובה לצרף לפחות תמונה אחת של הפריט
    photo = str(data.get("photo") or "")
    if not photo:
        errors.append("יש לצרף תמונה של הפריט")
    elif len(photo) > MAX_PHOTO_CHARS or not PHOTO_RE.match(photo):
        errors.append("התמונה לא תקינה או גדולה מדי (עד 2MB)")

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
        "photo": photo,
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
        insert into donations (donor_name, phone, item_name, category_id, description, point_id, photo)
        values (%(donor_name)s, %(phone)s, %(item_name)s, %(category_id)s, %(description)s, %(point_id)s, %(photo)s)
        returning id, status, created_at::text as created_at
        """,
        clean,
    ).fetchone()
    notify(conn, clean["phone"], f"תודה! קיבלנו את הצעת התרומה שלך (פנייה מס' {row['id']}). נעדכן אותך בכל שינוי בסטטוס.")
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


@bp.get("/donations/mine")
def my_donations():
    """מעקב תרומות (AB#273): כל ההצעות של התורם לפי מספר הטלפון שלו."""
    phone = normalize_phone(request.args.get("phone"))
    if not phone:
        return jsonify(error="מספר טלפון לא תקין (למשל 050-1234567)"), 400
    rows = get_conn().execute(
        """
        select d.id, d.item_name, d.status, p.name as point, d.created_at::text as created_at
        from donations d
        join points p on p.id = d.point_id
        where d.phone = %(phone)s
        order by d.id desc
        """,
        {"phone": phone},
    ).fetchall()
    for r in rows:
        r["status_text"] = STATUS_TEXT.get(r["status"], r["status"])
    return jsonify(rows)


def change_donation_status(conn, donation_id, status, note=None):
    """עדכון סטטוס של תרומה ושליחת הודעה לתורם (AB#273). מחזיר את התרומה, או None אם לא נמצאה."""
    row = conn.execute(
        """
        update donations set status = %(status)s
        where id = %(id)s
        returning id, phone, item_name, status
        """,
        {"id": donation_id, "status": status},
    ).fetchone()
    if row:
        text = f"עדכון לגבי התרומה שלך ({row['item_name']}, פנייה מס' {row['id']}): {STATUS_TEXT[status]}."
        if note:
            text += f" {note}"
        notify(conn, row["phone"], text)
    return row


@bp.post("/donations/<int:donation_id>/status")
def update_status(donation_id):
    """עדכון סטטוס תרומה על ידי צוות הגמ"ח. התורם מקבל הודעה על כל שינוי."""
    data = request.get_json(silent=True) or {}
    status = data.get("status")
    if status not in STATUS_TEXT:
        return jsonify(error="סטטוס לא תקין"), 400
    row = change_donation_status(get_conn(), donation_id, status, (data.get("note") or "").strip() or None)
    if not row:
        return jsonify(error="התרומה לא נמצאה"), 404
    return jsonify(id=row["id"], status=row["status"], status_text=STATUS_TEXT[row["status"]])


@bp.get("/notifications")
def my_notifications():
    """ההודעות שנשלחו למספר טלפון (לצפייה של המשתמש ולבדיקות)."""
    phone = normalize_phone(request.args.get("phone"))
    if not phone:
        return jsonify(error="מספר טלפון לא תקין"), 400
    rows = get_conn().execute(
        """
        select id, channel, message, created_at::text as created_at
        from notifications where phone = %(phone)s order by id desc limit 20
        """,
        {"phone": phone},
    ).fetchall()
    return jsonify(rows)
