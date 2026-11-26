"""קליטת החזרה (AB#194) ותיעוד נזק (AB#204) - החלק של רפאל.

סורקים (או מקלידים) את הקוד של כל יחידה שמוחזרת. אפשר להחזיר רק חלק מההזמנה.
כשכל היחידות חזרו ואין נזק, מסגרת הפיקדון משתחררת. יחידה עם נזק עוברת ל"בתיקון".
"""
import re

from flask import Blueprint, jsonify, request

from .db import get_conn
from .notify import notify

bp = Blueprint("returns", __name__, url_prefix="/api")

SEVERITY = {"light": "קל", "medium": "בינוני", "severe": "חמור"}
PHOTO_RE = re.compile(r"^data:image/(png|jpe?g|webp|gif);base64,[A-Za-z0-9+/=]+$")

RETURN_SQL = """
with target as (
    select ou.order_id, ou.unit_id
    from order_units ou
    join units u on u.id = ou.unit_id
    where ou.order_id = %(id)s and ou.returned_at is null and u.code = any(%(codes)s::text[])
),
marked as (
    update order_units ou set returned_at = now()
    from target t
    where ou.order_id = t.order_id and ou.unit_id = t.unit_id
    returning ou.unit_id
),
freed as (
    update units set status = case
        when exists (select 1 from damages d where d.unit_id = units.id and d.order_id = %(id)s) then 'repair'
        else 'available' end
    where id in (select unit_id from marked)
    returning id
),
remaining as (
    select count(*) as n from order_units
    where order_id = %(id)s and returned_at is null and unit_id not in (select unit_id from marked)
),
closed as (
    update orders set status = 'returned', returned_at = now(),
        deposit_status = case when exists (select 1 from damages where order_id = %(id)s) then 'held' else 'released' end
    where id = %(id)s and (select n from remaining) = 0 and exists (select 1 from marked)
    returning status, deposit_status
)
select (select count(*) from marked) as returned_now, (select n from remaining) as remaining,
       (select status from closed) as order_status, (select deposit_status from closed) as deposit_status
"""


@bp.post("/orders/<int:order_id>/return")
def receive_return(order_id):
    data = request.get_json(silent=True) or {}
    codes = sorted({str(c).strip().upper() for c in data.get("unit_codes") or [] if str(c).strip()})
    if not codes:
        return jsonify(error="יש לסרוק לפחות יחידה אחת"), 400
    conn = get_conn()
    order = conn.execute(
        """
        select o.id, o.code, o.phone, o.status, o.point_id,
               coalesce(array_agg(u.code) filter (where ou.returned_at is null), '{}') as open_codes
        from orders o
        left join order_units ou on ou.order_id = o.id
        left join units u on u.id = ou.unit_id
        where o.id = %(id)s
        group by o.id
        """,
        {"id": order_id},
    ).fetchone()
    if not order:
        return jsonify(error="ההזמנה לא נמצאה"), 404
    if order["point_id"] != data.get("point_id"):
        return jsonify(error="ההזמנה שייכת לנקודה אחרת"), 400
    if order["status"] != "picked_up":
        return jsonify(error="אפשר לקלוט החזרה רק להזמנה שנמסרה"), 409
    unknown = [c for c in codes if c not in order["open_codes"]]
    if unknown:
        return jsonify(error=f"היחידות האלה לא ממתינות להחזרה בהזמנה הזו: {', '.join(unknown)}"), 400

    res = conn.execute(RETURN_SQL, {"id": order_id, "codes": codes}).fetchone()
    if res["order_status"] == "returned":
        if res["deposit_status"] == "released":
            text = f"כל הציוד של הזמנה {order['code']} הוחזר תקין. מסגרת הפיקדון שוחררה. תודה!"
        else:
            text = f"הציוד של הזמנה {order['code']} הוחזר. נמצא נזק, ומנהל הנקודה ייצור איתך קשר לגבי הפיקדון."
        notify(conn, order["phone"], text)
    return jsonify(res)


@bp.post("/units/<code>/damage")
def report_damage(code):
    """תיעוד נזק ביחידה: חובה תמונה ותיאור, הדרגה מתוך רשימה, והיחידה עוברת לסטטוס "בתיקון"."""
    data = request.get_json(silent=True) or {}
    severity = data.get("severity")
    description = str(data.get("description") or "").strip()
    photo = str(data.get("photo") or "")
    errors = []
    if severity not in SEVERITY:
        errors.append("יש לבחור דרגת חומרה")
    if len(description) < 3:
        errors.append("יש לתאר את הנזק")
    if not PHOTO_RE.match(photo) or len(photo) > 3_000_000:
        errors.append("יש לצרף תמונה של הנזק (עד 2MB)")
    if errors:
        return jsonify(error=" · ".join(errors)), 400

    row = get_conn().execute(
        """
        with u as (
            update units set status = 'repair' where code = %(code)s returning id, code
        ),
        d as (
            insert into damages (unit_id, order_id, severity, description, photo)
            select u.id,
                   (select ou.order_id from order_units ou join orders o on o.id = ou.order_id
                    where ou.unit_id = u.id and o.status = 'picked_up' order by o.id desc limit 1),
                   %(severity)s, %(description)s, %(photo)s
            from u
            returning id, order_id
        )
        select d.id, d.order_id, u.code from d join u on true
        """,
        {"code": code.strip().upper(), "severity": severity, "description": description, "photo": photo},
    ).fetchone()
    if not row:
        return jsonify(error="היחידה לא נמצאה"), 404
    return jsonify({**row, "unit_status": "repair", "severity_text": SEVERITY[severity]}), 201
