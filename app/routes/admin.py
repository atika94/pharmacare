from datetime import date
from functools import wraps
import os
import uuid

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.database.connection import execute_query, fetch_all, fetch_one


admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "gif", "webp"}


def _save_image(upload):
    if not upload or not upload.filename:
        return None, None
    extension = secure_filename(upload.filename).rsplit(".", 1)[-1].lower()
    if extension not in ALLOWED_IMAGE_EXTENSIONS:
        return None, "Image must be JPG, JPEG, PNG, GIF, or WEBP."
    filename = f"{uuid.uuid4().hex}.{extension}"
    upload_directory = os.path.join("app", "static", "images", "medicines")
    os.makedirs(upload_directory, exist_ok=True)
    upload.save(os.path.join(upload_directory, filename))
    return filename, None


def admin_required(view):
    @wraps(view)
    @login_required
    def wrapped_view(*args, **kwargs):
        if not current_user.is_admin():
            abort(403)
        return view(*args, **kwargs)

    return wrapped_view


def _medicine_form_data():
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    manufacturer = request.form.get("manufacturer", "").strip()
    description = request.form.get("description", "").strip()
    expiry_date = request.form.get("expiry_date", "").strip() or None
    requires_prescription = 1 if request.form.get("requires_prescription") else 0

    try:
        price = float(request.form.get("price", ""))
        stock_quantity = int(request.form.get("stock_quantity", ""))
    except ValueError:
        return None, "Price must be a number and stock must be a whole number."

    if not name:
        return None, "Medicine name is required."
    if price < 0:
        return None, "Price cannot be negative."
    if stock_quantity < 0:
        return None, "Stock quantity cannot be negative."

    return {
        "name": name,
        "category": category or None,
        "manufacturer": manufacturer or None,
        "price": price,
        "stock_quantity": stock_quantity,
        "expiry_date": expiry_date,
        "description": description or None,
        "requires_prescription": requires_prescription,
    }, None


@admin_bp.route("")
@admin_required
def dashboard():
    medicines = fetch_all(
        """
        SELECT id, name, category, price, stock_quantity, expiry_date,
               requires_prescription, image_filename
        FROM medicines
        ORDER BY name COLLATE NOCASE
        """
    )


    low_stock = [medicine for medicine in medicines if medicine["stock_quantity"] <= 10]
    expired = fetch_all(
        """
        SELECT id, name, expiry_date
        FROM medicines
        WHERE expiry_date IS NOT NULL AND date(expiry_date) < date('now')
        ORDER BY expiry_date
        """
    )


@admin_bp.route("/orders")
@admin_required
def orders():
    orders_data = fetch_all(
        """
        SELECT orders.id, orders.total_amount, orders.pickup_location,
               orders.status, orders.created_at, users.name AS customer_name,
               users.email AS customer_email
        FROM orders
        JOIN users ON users.id = orders.user_id
        ORDER BY orders.created_at DESC, orders.id DESC
        """
    )
    return render_template("admin/orders.html", orders=orders_data)
    return render_template(
        "admin/dashboard.html",
        medicines=medicines,
        low_stock=low_stock,
        expired=expired,
        now_date=date.today().isoformat(),
    )


@admin_bp.route("/medicines/new", methods=["GET", "POST"])
@admin_required
def create_medicine():
    if request.method == "POST":
        data, error = _medicine_form_data()
        if error:
            flash(error, "danger")
            return render_template("admin/medicine_form.html", medicine=request.form, heading="Add medicine")

        image_filename, image_error = _save_image(request.files.get("image"))
        if image_error:
            flash(image_error, "danger")
            return render_template("admin/medicine_form.html", medicine=request.form, heading="Add medicine")

        data["image_filename"] = image_filename
        if execute_query(
            """
            INSERT INTO medicines
                (name, category, manufacturer, price, stock_quantity, expiry_date,
                  description, requires_prescription, image_filename)
              VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            tuple(data.values()),
        ):
            flash("Medicine added successfully.", "success")
            return redirect(url_for("admin.dashboard"))
        flash("Medicine could not be added.", "danger")

    return render_template("admin/medicine_form.html", medicine={}, heading="Add medicine")


@admin_bp.route("/medicines/<int:medicine_id>/edit", methods=["GET", "POST"])
@admin_required
def edit_medicine(medicine_id):
    medicine = fetch_one("SELECT * FROM medicines WHERE id = ?", (medicine_id,))
    if medicine is None:
        abort(404)

    if request.method == "POST":
        data, error = _medicine_form_data()
        if error:
            flash(error, "danger")
            return render_template("admin/medicine_form.html", medicine=request.form, heading="Edit medicine")

        image_filename, image_error = _save_image(request.files.get("image"))
        if image_error:
            flash(image_error, "danger")
            return render_template("admin/medicine_form.html", medicine=request.form, heading="Edit medicine")
        data["image_filename"] = image_filename or medicine["image_filename"]

        updated = execute_query(
            """
            UPDATE medicines
            SET name = ?, category = ?, manufacturer = ?, price = ?,
                stock_quantity = ?, expiry_date = ?, description = ?,
                requires_prescription = ?, image_filename = ?
            WHERE id = ?
            """,
            tuple(data.values()) + (medicine_id,),
        )
        if updated:
            flash("Medicine updated successfully.", "success")
            return redirect(url_for("admin.dashboard"))
        flash("Medicine could not be updated.", "danger")

    return render_template("admin/medicine_form.html", medicine=medicine, heading="Edit medicine")


@admin_bp.post("/medicines/<int:medicine_id>/delete")
@admin_required
def delete_medicine(medicine_id):
    if fetch_one("SELECT id FROM medicines WHERE id = ?", (medicine_id,)) is None:
        abort(404)
    if execute_query("DELETE FROM medicines WHERE id = ?", (medicine_id,)):
        flash("Medicine deleted successfully.", "success")
    else:
        flash("Medicine could not be deleted.", "danger")
    return redirect(url_for("admin.dashboard"))
