from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

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
    reviews = fetch_all(
        """
        SELECT reviews.rating, reviews.comment, reviews.created_at, users.name AS customer_name
        FROM reviews
        JOIN users ON users.id = reviews.user_id
        WHERE reviews.medicine_id = ?
        ORDER BY reviews.created_at DESC
        """,
        (medicine_id,),
    )
    average_rating = (
        sum(review["rating"] for review in reviews) / len(reviews) if reviews else 0
    )
    existing_review = None
    if current_user.is_authenticated:
        existing_review = fetch_one(
            "SELECT rating, comment FROM reviews WHERE medicine_id = ? AND user_id = ?",
            (medicine_id, current_user.id),
        )
    return render_template(
        "medicines/detail.html",
        medicine=Medicine(**medicine_data),
        reviews=reviews,
        average_rating=average_rating,
        existing_review=existing_review,
    )


@medicines_bp.post("/medicines/<int:medicine_id>/reviews")
@login_required
def add_review(medicine_id):
    medicine = fetch_one("SELECT id FROM medicines WHERE id = ?", (medicine_id,))
    if medicine is None:
        return redirect(url_for("medicines.list_medicines"))

    try:
        rating = int(request.form.get("rating", ""))
    except ValueError:
        rating = 0
    comment = request.form.get("comment", "").strip()
    if rating not in range(1, 6):
        flash("Please choose a rating from 1 to 5 stars.", "danger")
        return redirect(url_for("medicines.medicine_detail", medicine_id=medicine_id))
    if len(comment) > 1000:
        flash("Review comments must be 1000 characters or fewer.", "danger")
        return redirect(url_for("medicines.medicine_detail", medicine_id=medicine_id))

    if fetch_one(
        "SELECT id FROM reviews WHERE medicine_id = ? AND user_id = ?",
        (medicine_id, current_user.id),
    ):
        flash("You have already reviewed this medicine.", "info")
    elif fetch_one(
        """
        SELECT order_items.id
        FROM order_items
        JOIN orders ON orders.id = order_items.order_id
        WHERE order_items.medicine_id = ? AND orders.user_id = ?
          AND orders.status = 'delivered'
        LIMIT 1
        """,
        (medicine_id, current_user.id),
    ) is None:
        flash("You can review medicines after a delivered order.", "warning")
    else:
        from app.database.connection import execute_query
        if execute_query(
            """
            INSERT INTO reviews (user_id, medicine_id, rating, comment)
            VALUES (?, ?, ?, ?)
            """,
            (current_user.id, medicine_id, rating, comment or None),
        ):
            flash("Thank you for your review.", "success")
        else:
            flash("Your review could not be saved.", "danger")
    return redirect(url_for("medicines.medicine_detail", medicine_id=medicine_id))
