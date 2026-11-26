"""לוח בקרה (KPI) למנהל הרשת (AB#300) - החלק של רפאל.

המדדים מחושבים פעם ביום לכל נקודה (או לכל הרשת) ונשמרים בטבלת kpi_daily,
כך שהלוח נטען מהר גם כשיש הרבה נתונים.
"""
from flask import Blueprint, jsonify, request

from .db import get_conn

bp = Blueprint("kpi", __name__, url_prefix="/api")

COMPUTE_SQL = """
with scope as (select %(point)s::int as point_id),
o as (select * from orders where (select point_id from scope) = 0 or point_id = (select point_id from scope)),
u as (select * from units where (select point_id from scope) = 0 or point_id = (select point_id from scope)),
d as (select * from donations where (select point_id from scope) = 0 or point_id = (select point_id from scope)),
stats as (
    select json_build_object(
        'active_loans',      (select count(*) from o where status = 'picked_up'),
        'overdue_loans',     (select count(*) from o where status = 'picked_up' and end_date < current_date),
        'reserved_orders',   (select count(*) from o where status = 'reserved'),
        'loans_last_30_days',(select count(*) from o where picked_up_at >= now() - interval '30 days'),
        'units_available',   (select count(*) from u where status = 'available'),
        'units_loaned',      (select count(*) from u where status = 'loaned'),
        'units_in_repair',   (select count(*) from u where status = 'repair'),
        'pending_donations', (select count(*) from d where status = 'pending'),
        'utilization_pct',   (select round(100.0 * count(*) filter (where status = 'loaned') / nullif(count(*), 0)) from u)
    ) as data
)
insert into kpi_daily (day, point_id, data)
select current_date, (select point_id from scope), data from stats
on conflict (day, point_id) do update set data = kpi_daily.data
returning day::text as day, point_id, data
"""


@bp.get("/admin/kpi")
def kpi():
    point = request.args.get("point_id", default=0, type=int) or 0
    conn = get_conn()
    row = conn.execute(
        "select day::text as day, point_id, data from kpi_daily where day = current_date and point_id = %(point)s",
        {"point": point},
    ).fetchone()
    if not row:  # הטעינה הראשונה של היום מחשבת ושומרת
        row = conn.execute(COMPUTE_SQL, {"point": point}).fetchone()
    return jsonify(row)
