"""קטלוג הפריטים - קריאה מבסיס הנתונים (בקשה של אורי)."""
from flask import Blueprint, jsonify, request

from .db import get_conn

bp = Blueprint("items", __name__, url_prefix="/api")


@bp.get("/items")
def list_items():
    """פריטי הקטלוג עם מספר היחידות הזמינות. סינון אופציונלי: ?category=<id>&q=<טקסט>"""
    category = request.args.get("category", type=int)
    q = (request.args.get("q") or "").strip() or None
    rows = get_conn().execute(
        """
        select i.id, i.name, i.description, i.deposit_amount, i.max_loan_days,
               c.id as category_id, c.name as category,
               count(u.id) filter (where u.status = 'available') as available_units
        from items i
        join categories c on c.id = i.category_id
        left join units u on u.item_id = i.id
        where (%(category)s::int is null or i.category_id = %(category)s::int)
          and (%(q)s::text is null
               or i.name ilike '%%' || %(q)s::text || '%%'
               or i.description ilike '%%' || %(q)s::text || '%%')
        group by i.id, c.id
        order by c.sort_order, i.name
        """,
        {"category": category, "q": q},
    ).fetchall()
    return jsonify(rows)
