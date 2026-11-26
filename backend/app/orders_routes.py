"""יצירת הזמנה: בחירת נקודה, תאריכים ושעת איסוף (AB#114), וההשאלות שלי (AB#151) - החלק של אורי."""
import secrets
from datetime import date

from flask import Blueprint, jsonify, request

from .booking import UNIT_BUSY_SQL, normalize_phone, parse_date, rest_day_reason
from .db import get_conn
from .notify import notify

bp = Blueprint("orders", __name__, url_prefix="/api")

STATUS_TEXT = {"reserved": "שוריינה, ממתינה לאיסוף", "picked_up": "בהשאלה", "returned": "הוחזרה", "cancelled": "בוטלה"}

CREATE_ORDER_SQL = f"""
with req(item_id, qty) as (
    select * from unnest(%(item_ids)s::int[], %(qtys)s::int[])
),
free as (
    select u.id, u.item_id, row_number() over (partition by u.item_id order by u.id) as rn
    from units u
    where u.point_id = %(point)s
      and u.status in ('available', 'loaned')
      and u.item_id in (select item_id from req)
      and not {UNIT_BUSY_SQL}
),
chosen as (
    select f.id, f.item_id from free f join req r on r.item_id = f.item_id and f.rn <= r.qty
),
enough as (
    select (select count(*) from chosen) = (select coalesce(sum(qty), 0) from req) as ok
),
new_order as (
    insert into orders (code, borrower_name, phone, point_id, start_date, end_date, pickup_time, deposit_total)
    select %(code)s, %(name)s, %(phone)s, %(point)s, %(start)s, %(end)s, %(pickup)s,
           (select coalesce(sum(i.deposit_amount * r.qty), 0) from req r join items i on i.id = r.item_id)
    where (select ok from enough)
    returning id, code, deposit_total
),
assigned as (
    insert into order_units (order_id, unit_id)
    select n.id, c.id from new_order n cross join chosen c
    returning unit_id
),
cleared as (
    delete from cart_items where phone = %(phone)s and exists (select 1 from new_order) returning item_id
)
select n.id, n.code, n.deposit_total, (select count(*) from assigned) as units from new_order n
"""


def _validate(conn, data):
    errors = []
    name = str(data.get("name") or "").strip()
    phone = normalize_phone(data.get("phone"))
    start, end = parse_date(data.get("start_date")), parse_date(data.get("end_date"))
    pickup = str(data.get("pickup_time") or "")[:5]
    try:
        point_id = int(data.get("point_id"))
    except (TypeError, ValueError):
        point_id = None

    if not 2 <= len(name) <= 60:
        errors.append("יש למלא שם מלא")
    if not phone:
        errors.append("מספר טלפון לא תקין (למשל 050-1234567)")
    if not point_id:
        errors.append("יש לבחור נקודת איסוף")
    if not start or not end:
        errors.append("יש לבחור תאריך איסוף ותאריך החזרה")
    elif start < date.today():
        errors.append("תאריך האיסוף כבר עבר")
    elif end < start:
        errors.append("תאריך ההחזרה לפני תאריך האיסוף")

    items = data.get("items")
    if items is None and phone:  # ברירת מחדל: מה שבעגלה
        items = conn.execute("select item_id, qty from cart_items where phone = %(phone)s", {"phone": phone}).fetchall()
    try:
        items = [{"item_id": int(i["item_id"]), "qty": int(i["qty"])} for i in items or [] if int(i["qty"]) > 0]
    except (TypeError, ValueError, KeyError):
        items = []
        errors.append("רשימת הפריטים לא תקינה")
    if not items and not errors:
        errors.append("העגלה ריקה")
    if errors:
        return None, errors

    # שבתות וחגים חסומים לפי הלוח העברי
    holidays = {r["day"]: r["name"] for r in conn.execute(
        "select day::text as day, name from holidays where day in (%(start)s::date, %(end)s::date)",
        {"start": start.isoformat(), "end": end.isoformat()},
    ).fetchall()}
    for label, day in (("האיסוף", start), ("ההחזרה", end)):
        reason = rest_day_reason(day, holidays)
        if reason:
            errors.append(f"אי אפשר לקבוע את {label} ב{reason} ({day.strftime('%d/%m/%Y')})")

    # משך ההשאלה עד המקסימום שבמדיניות של הפריטים
    limit = conn.execute(
        "select min(max_loan_days) as days from items where id = any(%(ids)s::int[])",
        {"ids": [i["item_id"] for i in items]},
    ).fetchone()
    days = (end - start).days
    if limit and limit["days"] is not None and days > limit["days"]:
        errors.append(f"משך ההשאלה המקסימלי לפריטים שבחרתם הוא {limit['days']} ימים")

    # שעת האיסוף בתוך שעות הפעילות של הנקודה
    point = conn.execute(
        """select name, to_char(open_time, 'HH24:MI') as open_time, to_char(close_time, 'HH24:MI') as close_time
           from points where id = %(id)s and is_active""",
        {"id": point_id},
    ).fetchone()
    if not point:
        errors.append("נקודת האיסוף לא נמצאה")
    elif not (len(pickup) == 5 and point["open_time"] <= pickup < point["close_time"]):
        errors.append(f"שעת האיסוף צריכה להיות בשעות הפעילות של הנקודה ({point['open_time']}-{point['close_time']})")
    if errors:
        return None, errors

    return {
        "name": name, "phone": phone, "point": point_id, "point_name": point["name"],
        "start": start.isoformat(), "end": end.isoformat(), "pickup": pickup,
        "item_ids": [i["item_id"] for i in items], "qtys": [i["qty"] for i in items],
    }, []


@bp.post("/orders")
def create_order():
    conn = get_conn()
    clean, errors = _validate(conn, request.get_json(silent=True) or {})
    if errors:
        return jsonify(error=" · ".join(errors)), 400
    clean["code"] = f"GH-{secrets.randbelow(900000) + 100000}"
    row = conn.execute(CREATE_ORDER_SQL, clean).fetchone()
    if not row:
        return jsonify(error="אין מספיק יחידות פנויות בנקודה הזו בתאריכים שבחרתם"), 409
    notify(conn, clean["phone"],
           f"ההזמנה {row['code']} אושרה: איסוף ב{clean['point_name']} בתאריך {clean['start']} בשעה {clean['pickup']}.")
    return jsonify(row), 201


@bp.get("/loans")
def my_loans():
    """ההשאלות שלי (AB#151): פעילות והיסטוריה, ממוינות לפי תאריך ההחזרה, עם סימון איחור ופרטי הנקודה."""
    phone = normalize_phone(request.args.get("phone"))
    if not phone:
        return jsonify(error="מספר טלפון לא תקין (למשל 050-1234567)"), 400
    rows = get_conn().execute(
        """
        select o.id, o.code, o.status, o.start_date::text as start_date, o.end_date::text as end_date,
               to_char(o.pickup_time, 'HH24:MI') as pickup_time, o.deposit_total,
               (o.status = 'picked_up' and o.end_date < current_date) as is_overdue,
               greatest(current_date - o.end_date, 0) as days_late,
               p.name as point, p.address as point_address, p.opening_hours as point_hours,
               coalesce((select json_agg(json_build_object('item', x.name, 'qty', x.qty) order by x.name)
                         from (select i.name, count(*) as qty from order_units ou
                               join units u on u.id = ou.unit_id join items i on i.id = u.item_id
                               where ou.order_id = o.id group by i.name) x), '[]') as items
        from orders o
        join points p on p.id = o.point_id
        where o.phone = %(phone)s and o.status <> 'cancelled'
        order by (o.status in ('reserved', 'picked_up')) desc, o.end_date
        """,
        {"phone": phone},
    ).fetchall()
    for r in rows:
        r["status_text"] = "באיחור" if r["is_overdue"] else STATUS_TEXT.get(r["status"], r["status"])
    return jsonify(rows)
