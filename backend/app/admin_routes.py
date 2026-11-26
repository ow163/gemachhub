"""ניהול רשת: אישור או דחייה של תרומות (AB#279) - החלק של אורי."""
from flask import Blueprint, jsonify, request

from .db import get_conn
from .donations_routes import STATUS_TEXT, change_donation_status

bp = Blueprint("admin", __name__, url_prefix="/api")


@bp.get("/admin/donations")
def pending_donations():
    status = request.args.get("status", "pending")
    if status not in STATUS_TEXT:
        return jsonify(error="סטטוס לא תקין"), 400
    rows = get_conn().execute(
        """
        select d.id, d.donor_name, d.phone, d.item_name, d.description, d.photo, d.status,
               c.name as category, p.name as point, d.created_at::text as created_at, d.decision_reason
        from donations d
        join points p on p.id = d.point_id
        left join categories c on c.id = d.category_id
        where d.status = %(status)s
        order by d.id
        """,
        {"status": status},
    ).fetchall()
    return jsonify(rows)


@bp.post("/donations/<int:donation_id>/decision")
def decide(donation_id):
    """החלטה על תרומה ממתינה. בדחייה חובה לכתוב נימוק. התורם מקבל הודעה, וההחלטה נרשמת ביומן."""
    data = request.get_json(silent=True) or {}
    decision = data.get("decision")
    reason = str(data.get("reason") or "").strip()
    if decision not in ("approve", "reject"):
        return jsonify(error="יש לבחור אישור או דחייה"), 400
    if decision == "reject" and len(reason) < 3:
        return jsonify(error="בדחייה חובה לכתוב נימוק"), 400

    conn = get_conn()
    current = conn.execute("select status from donations where id = %(id)s", {"id": donation_id}).fetchone()
    if not current:
        return jsonify(error="התרומה לא נמצאה"), 404
    if current["status"] != "pending":
        return jsonify(error="כבר התקבלה החלטה על התרומה הזו"), 409

    status = "approved" if decision == "approve" else "rejected"
    note = f"הנימוק: {reason}" if status == "rejected" else "נתאם איתך את המסירה בנקודה."
    row = change_donation_status(conn, donation_id, status, note)
    conn.execute(
        """
        update donations set decision_reason = %(reason)s, decided_at = now() where id = %(id)s returning id
        """,
        {"id": donation_id, "reason": reason or None},
    ).fetchone()
    conn.execute(
        """
        insert into audit_log (action, entity, entity_id, details)
        values (%(action)s, 'donation', %(id)s, %(details)s) returning id
        """,
        {"action": f"donation_{status}", "id": donation_id, "details": reason},
    ).fetchone()
    return jsonify(id=row["id"], status=status, status_text=STATUS_TEXT[status])


@bp.get("/admin/audit")
def audit_log():
    rows = get_conn().execute(
        "select id, action, entity, entity_id, details, actor, created_at::text as created_at from audit_log order by id desc limit 50"
    ).fetchall()
    return jsonify(rows)
