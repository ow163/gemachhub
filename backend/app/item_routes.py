"""כרטיס פריט מפורט (AB#103): תמונות, פיקדון, תקופת השאלה וזמינות לפי נקודות (החלק של רפאל)."""
from flask import Blueprint, jsonify

from .db import get_conn

bp = Blueprint("item", __name__, url_prefix="/api")


@bp.get("/items/<int:item_id>")
def item_details(item_id):
    row = get_conn().execute(
        """
        select i.id, i.name, i.description, i.deposit_amount, i.max_loan_days, i.images,
               c.id as category_id, c.name as category,
               coalesce((
                   select json_agg(json_build_object(
                              'point_id', p.id, 'point', p.name, 'address', p.address,
                              'opening_hours', p.opening_hours, 'available', a.available)
                          order by a.available desc, p.id)
                   from (select u.point_id, count(*) filter (where u.status = 'available') as available
                         from units u where u.item_id = i.id group by u.point_id) a
                   join points p on p.id = a.point_id and p.is_active
               ), '[]') as availability
        from items i
        join categories c on c.id = i.category_id
        where i.id = %(id)s
        """,
        {"id": item_id},
    ).fetchone()
    if not row:
        return jsonify(error="הפריט לא נמצא"), 404
    return jsonify(row)
