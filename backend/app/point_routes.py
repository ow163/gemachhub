"""עמדת המתנדב בנקודה: איסופים להיום (AB#173) ומסירת הזמנה לפי קוד או טלפון (AB#178) - החלק של אורי."""
from datetime import date

from flask import Blueprint, jsonify, request

from .booking import normalize_phone, parse_date
from .db import get_conn
from .notify import notify

bp = Blueprint("point", __name__, url_prefix="/api")

ITEMS_JSON = """
    coalesce((select json_agg(json_build_object('item', x.name, 'qty', x.qty, 'codes', x.codes) order by x.name)
              from (select i.name, count(*) as qty, array_agg(u.code order by u.code) as codes
                    from order_units ou join units u on u.id = ou.unit_id join items i on i.id = u.item_id
                    where ou.order_id = o.id group by i.name) x), '[]')
"""

ORDER_SQL = f"""
    select o.id, o.code, o.borrower_name, o.phone, o.status, o.point_id, p.name as point,
           o.start_date::text as start_date, o.end_date::text as end_date,
           to_char(o.pickup_time, 'HH24:MI') as pickup_time, o.deposit_total, o.deposit_status,
           {ITEMS_JSON} as items
    from orders o join points p on p.id = o.point_id
"""


@bp.get("/points/<int:point_id>/pickups")
def pickups(point_id):
    """איסופים ליום מסוים (ברירת מחדל: היום), ממוינים לפי שעה, עם פריטים וכמויות ומי כבר אסף."""
    day = parse_date(request.args.get("date")) or date.today()
    rows = get_conn().execute(
        ORDER_SQL + """
        where o.point_id = %(point)s and o.start_date = %(day)s::date and o.status in ('reserved', 'picked_up')
        order by o.pickup_time, o.id
        """,
        {"point": point_id, "day": day.isoformat()},
    ).fetchall()
    for r in rows:
        r["collected"] = r["status"] == "picked_up"
    return jsonify(day=day.isoformat(), pickups=rows)


def _with_deposit_flag(order):
    order["deposit_ok"] = order["deposit_status"] == "held"
    return order


@bp.get("/orders/lookup")
def lookup_order():
    """איתור הזמנה לפי קוד (מסריקת QR או הקלדה) או לפי טלפון. הזמנה של נקודה אחרת מחזירה שגיאה."""
    point_id = request.args.get("point_id", type=int)
    code = (request.args.get("code") or "").strip().upper()
    phone_arg = request.args.get("phone")
    if not point_id:
        return jsonify(error="יש לבחור נקודה"), 400
    conn = get_conn()
    if code:
        rows = conn.execute(ORDER_SQL + " where o.code = %(code)s", {"code": code}).fetchall()
    elif phone_arg:
        phone = normalize_phone(phone_arg)
        if not phone:
            return jsonify(error="מספר טלפון לא תקין"), 400
        rows = conn.execute(
            ORDER_SQL + " where o.phone = %(phone)s and o.status in ('reserved', 'picked_up') order by o.start_date",
            {"phone": phone},
        ).fetchall()
    else:
        return jsonify(error="יש להזין קוד הזמנה או מספר טלפון"), 400

    if not rows:
        return jsonify(error="לא נמצאה הזמנה"), 404
    here = [r for r in rows if r["point_id"] == point_id]
    if not here:
        return jsonify(error=f"ההזמנה שייכת לנקודה אחרת ({rows[0]['point']})"), 400
    return jsonify([_with_deposit_flag(r) for r in here])


@bp.post("/orders/<int:order_id>/handover")
def handover(order_id):
    """מסירת הציוד לשואל: ההזמנה עוברת ל'בהשאלה' והיחידות ל'מושאל'."""
    point_id = (request.get_json(silent=True) or {}).get("point_id")
    conn = get_conn()
    row = conn.execute(
        """
        with o as (
            update orders set status = 'picked_up', picked_up_at = now()
            where id = %(id)s and point_id = %(point)s and status = 'reserved'
              and start_date <= current_date and deposit_status = 'held'
            returning id, code, phone, end_date
        ),
        u as (
            update units set status = 'loaned'
            where id in (select unit_id from order_units where order_id in (select id from o))
            returning id
        )
        select o.id, o.code, o.phone, o.end_date::text as end_date, (select count(*) from u) as units from o
        """,
        {"id": order_id, "point": point_id},
    ).fetchone()
    if not row:
        return jsonify(error="אי אפשר למסור: ההזמנה לא נמצאה בנקודה הזו, כבר נמסרה, מתוכננת ליום אחר או שהפיקדון לא בתוקף"), 409
    notify(conn, row["phone"], f"הציוד של הזמנה {row['code']} נמסר לך. יש להחזיר עד {row['end_date']}. תודה!")
    return jsonify(row)
