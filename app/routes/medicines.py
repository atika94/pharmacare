from flask import Blueprint, render_template, request

from app.database.connection import fetch_all, fetch_one
from app.models.medicine import Medicine


medicines_bp = Blueprint("medicines", __name__)


@medicines_bp.route("/medicines")
def list_medicines():
    search = request.args.get("q", "").strip()
    search_pattern = f"%{search}%"

    medicines_data = fetch_all(
        """
        SELECT id, name, category, manufacturer, price, stock_quantity,
               expiry_date, description, requires_prescription, image_filename
        FROM medicines
        WHERE name LIKE ?
           OR category LIKE ?
           OR manufacturer LIKE ?
           OR description LIKE ?
        ORDER BY name COLLATE NOCASE
        """,
        (search_pattern, search_pattern, search_pattern, search_pattern),
    )

    medicines = [Medicine(**medicine) for medicine in medicines_data]
    return render_template("medicines/list.html", medicines=medicines, search=search)


@medicines_bp.route("/medicines/<int:medicine_id>")
def medicine_detail(medicine_id):
    medicine_data = fetch_one(
        """
        SELECT id, name, category, manufacturer, price, stock_quantity,
               expiry_date, description, requires_prescription, image_filename
        FROM medicines
        WHERE id = ?
        """,
        (medicine_id,),
    )
    if medicine_data is None:
        from flask import abort

        abort(404)
    return render_template("medicines/detail.html", medicine=Medicine(**medicine_data))
