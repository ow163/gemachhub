"""עגלת הזמנה (AB#109): נשמרת בשרת לפי מספר הטלפון, ולא מאפשרת כמות גדולה מהזמין (החלק של אורי)."""
from flask import Blueprint, jsonify, request

from .booking import normalize_phone
from .db import get_conn

bp = Blueprint("cart", __name__, url_prefix="/api")

CART_SQL = """
    select c.item_id, c.qty, i.name, i.deposit_amount, i.max_loan_days,
           (select count(*) from units u where u.item_id = i.id and u.status = 'available') as available_units
    from cart_items c
    join items i on i.id = c.item_id
    where c.phone = %(phone)s
    order by c.updated_at
"""


def cart_body(rows):
    total = sum(r["deposit_amount"] * r["qty"] for r in rows)
    return {"items": rows, "deposit_total": total, "count": sum(r["qty"] for r in rows)}


@bp.get("/cart")
def get_cart():
    phone = normalize_phone(request.args.get("phone"))
    if not phone:
        return jsonify(error="מספר טלפון לא תקין (למשל 050-1234567)"), 400
    return jsonify(cart_body(get_conn().execute(CART_SQL, {"phone": phone}).fetchall()))


@bp.put("/cart")
def set_cart_item():
    """הוספה או עדכון של כמות. כמות 0 מוחקת את הפריט מהעגלה."""
    data = request.get_json(silent=True) or {}
    phone = normalize_phone(data.get("phone"))
    try:
        item_id, qty = int(data.get("item_id")), int(data.get("qty"))
    except (TypeError, ValueError):
        return jsonify(error="פריט או כמות לא תקינים"), 400
    if not phone:
        return jsonify(error="מספר טלפון לא תקין (למשל 050-1234567)"), 400
    if qty < 0:
        return jsonify(error="כמות לא תקינה"), 400

    conn = get_conn()
    if qty == 0:
        conn.execute("delete from cart_items where phone = %(phone)s and item_id = %(item)s returning item_id",
                     {"phone": phone, "item": item_id}).fetchall()
    else:
        item = conn.execute(
            """
            select i.name, (select count(*) from units u where u.item_id = i.id and u.status = 'available') as available_units
            from items i where i.id = %(item)s
            """,
            {"item": item_id},
        ).fetchone()
        if not item:
            return jsonify(error="הפריט לא נמצא"), 404
        if qty > item["available_units"]:
            n = item["available_units"]
            return jsonify(error=f"אפשר להזמין עד {n} יחידות של {item['name']}" if n else f"{item['name']} לא זמין כרגע"), 400
        conn.execute(
            """
            insert into cart_items (phone, item_id, qty) values (%(phone)s, %(item)s, %(qty)s)
            on conflict (phone, item_id) do update set qty = excluded.qty, updated_at = now()
            returning item_id
            """,
            {"phone": phone, "item": item_id, "qty": qty},
        ).fetchone()
    return jsonify(cart_body(conn.execute(CART_SQL, {"phone": phone}).fetchall()))
