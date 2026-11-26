"""רשימת השאלות באיחור בנקודה (AB#215): ממוינת לפי ימי האיחור, עם טלפון ופריטים (החלק של רפאל).

הרשימה מחושבת מול התאריך של היום בכל טעינה, כך שהיא מתעדכנת כל יום מעצמה.
"""
from flask import Blueprint, jsonify

from .db import get_conn

bp = Blueprint("overdue", __name__, url_prefix="/api")


@bp.get("/points/<int:point_id>/overdue")
def overdue_loans(point_id):
    rows = get_conn().execute(
        """
        select o.id, o.code, o.borrower_name, o.phone, o.end_date::text as end_date,
               current_date - o.end_date as days_late,
               coalesce((select json_agg(json_build_object('item', x.name, 'qty', x.qty) order by x.name)
                         from (select i.name, count(*) as qty from order_units ou
                               join units u on u.id = ou.unit_id join items i on i.id = u.item_id
                               where ou.order_id = o.id and ou.returned_at is null group by i.name) x), '[]') as items
        from orders o
        where o.point_id = %(point)s
          and o.status = 'picked_up'
          and o.end_date < current_date
        order by days_late desc, o.id
        """,
        {"point": point_id},
    ).fetchall()
    return jsonify(rows)
