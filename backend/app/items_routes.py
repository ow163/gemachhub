"""קטלוג הפריטים - קריאה מבסיס הנתונים (בקשה של אורי)."""
import re

from flask import Blueprint, jsonify, request

from .booking import UNIT_BUSY_SQL, parse_date
from .db import get_conn

bp = Blueprint("items", __name__, url_prefix="/api")

NIQQUD_RE = re.compile(r"[\u0591-\u05BD\u05BF\u05C1\u05C2\u05C4\u05C5\u05C7]")


def normalize_query(text):
    """ניקוי טקסט חיפוש (AB#93): הסרת ניקוד וטעמים, ורווח אחד בין מילים."""
    text = NIQQUD_RE.sub("", text or "")
    return " ".join(text.split()) or None


# AB#98: זמינות בטווח תאריכים - יחידות שלא תפוסות באף הזמנה חופפת, ומתי פריט לא זמין יתפנה
RANGE_SQL = f"""
    select i.id, i.name, i.description, i.deposit_amount, i.max_loan_days,
           c.id as category_id, c.name as category,
           count(u.id) filter (where u.status in ('available', 'loaned') and not {UNIT_BUSY_SQL}) as available_units,
           min(busy.free_from) filter (where u.status in ('available', 'loaned'))::text as next_free_date
    from items i
    join categories c on c.id = i.category_id
    left join units u on u.item_id = i.id and (%(point)s::int is null or u.point_id = %(point)s::int)
    left join lateral (
        select max(o.end_date) + 1 as free_from
        from order_units ou join orders o on o.id = ou.order_id
        where ou.unit_id = u.id and ou.returned_at is null
          and o.status in ('reserved', 'picked_up') and o.end_date >= current_date
    ) busy on true
    where (%(category)s::int is null or i.category_id = %(category)s::int)
      and (%(q)s::text is null
           or i.name ilike '%%' || %(q)s::text || '%%'
           or i.description ilike '%%' || %(q)s::text || '%%')
    group by i.id, c.id
    order by c.sort_order, i.name
"""


@bp.get("/items")
def list_items():
    """פריטי הקטלוג עם מספר היחידות הזמינות.
    סינון אופציונלי: ?category=<id>&q=<טקסט>, ולזמינות בתאריכים: &start=YYYY-MM-DD&end=YYYY-MM-DD&point=<id>"""
    category = request.args.get("category", type=int)
    q = normalize_query(request.args.get("q"))
    if request.args.get("start") or request.args.get("end"):
        start, end = parse_date(request.args.get("start")), parse_date(request.args.get("end"))
        if not start or not end or end < start:
            return jsonify(error="טווח תאריכים לא תקין"), 400
        params = {"category": category, "q": q, "start": start.isoformat(), "end": end.isoformat(),
                  "point": request.args.get("point", type=int)}
        rows = get_conn().execute(RANGE_SQL, params).fetchall()
        for r in rows:
            if r["available_units"]:
                r["next_free_date"] = None
        return jsonify(rows)
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
