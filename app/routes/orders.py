from datetime import datetime, timedelta
import os
import uuid

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required
from werkzeug.utils import secure_filename

from app.database.connection import get_connection, fetch_all, fetch_one


orders_bp = Blueprint("orders", __name__)
ALLOWED_PRESCRIPTION_EXTENSIONS = {"jpg", "jpeg", "png", "pdf"}


def expire_unverified_orders():
    connection = get_connection()
    if connection is None:
        return
    cursor = connection.cursor()
    try:
        cutoff = (datetime.utcnow() - timedelta(minutes=30)).strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "SELECT id FROM orders WHERE status = 'pending_verification' AND created_at <= ?",
            (cutoff,),
        )
        order_ids = [row[0] for row in cursor.fetchall()]
        for order_id in order_ids:
            cursor.execute(
                "SELECT medicine_id, quantity FROM order_items WHERE order_id = ?",
                (order_id,),
            )
            for medicine_id, quantity in cursor.fetchall():
                cursor.execute(
                    "UPDATE medicines SET stock_quantity = stock_quantity + ? WHERE id = ?",
                    (quantity, medicine_id),
                )
            cursor.execute("UPDATE orders SET status = 'cancelled' WHERE id = ?", (order_id,))
        connection.commit()
    finally:
        cursor.close()
        connection.close()


def _save_prescription(upload):
    if not upload or not upload.filename:
        return None, "A prescription file is required for prescription medicines."
    safe_name = secure_filename(upload.filename)
    extension = safe_name.rsplit(".", 1)[-1].lower() if "." in safe_name else ""
    if extension not in ALLOWED_PRESCRIPTION_EXTENSIONS:
        return None, "Prescription must be a PDF, JPG, JPEG, or PNG file."
    filename = f"{uuid.uuid4().hex}.{extension}"
    upload_directory = os.path.join(current_app.instance_path, "prescriptions")
    os.makedirs(upload_directory, exist_ok=True)
    upload.save(os.path.join(upload_directory, filename))
    return filename, None


def _cart_items():
    cart = session.get("cart", {})
    if not cart:
        return [], 0

    ids = [int(medicine_id) for medicine_id in cart]
    placeholders = ", ".join("?" for _ in ids)
    medicines = fetch_all(
        f"""
        SELECT id, name, price, stock_quantity, requires_prescription
        FROM medicines
        WHERE id IN ({placeholders})
        ORDER BY name COLLATE NOCASE
        """,
        ids,
    )

    items = []
    total = 0
    for medicine in medicines:
        quantity = max(0, int(cart.get(str(medicine["id"]), 0)))
        if quantity == 0:
            continue
        subtotal = float(medicine["price"]) * quantity
        items.append({"medicine": medicine, "quantity": quantity, "subtotal": subtotal})
        total += subtotal
    return items, total


@orders_bp.route("/cart")
def cart():
    items, total = _cart_items()
    return render_template("orders/cart.html", items=items, total=total)


@orders_bp.route("/cart/add/<int:medicine_id>", methods=["POST"])
@login_required
def add_to_cart(medicine_id):
    medicine = fetch_one(
        "SELECT id, name, stock_quantity FROM medicines WHERE id = ?",
        (medicine_id,),
    )
    if medicine is None:
        flash("Medicine not found.", "danger")
        return redirect(url_for("medicines.list_medicines"))

    if medicine["stock_quantity"] < 1:
        flash("This medicine is out of stock.", "danger")
        return redirect(url_for("medicines.list_medicines"))

    cart_data = session.get("cart", {})
    current_quantity = int(cart_data.get(str(medicine_id), 0))
    if current_quantity >= medicine["stock_quantity"]:
        flash("You cannot add more than the available stock.", "warning")
    else:
        cart_data[str(medicine_id)] = current_quantity + 1
        session["cart"] = cart_data
        flash(f"{medicine['name']} added to your cart.", "success")
    return redirect(request.referrer or url_for("medicines.list_medicines"))


@orders_bp.route("/cart/update", methods=["POST"])
@login_required
def update_cart():
    cart_data = session.get("cart", {})
    for medicine_id, value in request.form.items():
        if not medicine_id.isdigit():
            continue
        try:
            quantity = int(value)
        except ValueError:
            quantity = 0
        if quantity <= 0:
            cart_data.pop(medicine_id, None)
        else:
            cart_data[medicine_id] = quantity
    session["cart"] = cart_data
    flash("Cart updated.", "success")
    return redirect(url_for("orders.cart"))


@orders_bp.route("/checkout", methods=["GET", "POST"])
@login_required
def checkout():
    expire_unverified_orders()
    items, total = _cart_items()
    if not items:
        flash("Your cart is empty.", "info")
        return redirect(url_for("orders.cart"))

    if request.method == "POST":
        connection = get_connection()
        try:
            cursor = connection.cursor()
            for item in items:
                cursor.execute(
                    "SELECT stock_quantity FROM medicines WHERE id = ?",
                    (item["medicine"]["id"],),
                )
                stock = cursor.fetchone()[0]
                if item["quantity"] > stock:
                    connection.rollback()
                    flash(f"Not enough stock for {item['medicine']['name']}.", "danger")
                    return redirect(url_for("orders.cart"))

            requires_prescription = any(item["medicine"]["requires_prescription"] for item in items)
            prescription_filename = None
            if requires_prescription:
                prescription_filename, prescription_error = _save_prescription(request.files.get("prescription"))
                if prescription_error:
                    connection.rollback()
                    flash(prescription_error, "danger")
                    return render_template("orders/checkout.html", items=items, total=total)
            pickup_location = request.form.get("pickup_location", "").strip()
            if not pickup_location:
                connection.rollback()
                flash("Pickup location is required.", "danger")
                return render_template("orders/checkout.html", items=items, total=total)

            status = "pending_verification" if requires_prescription else "pending"
            cursor.execute(
                """
                INSERT INTO orders
                    (user_id, total_amount, pickup_location, status, prescription_filename)
                VALUES (?, ?, ?, ?, ?)
                """,
                (current_user.id, total, pickup_location, status, prescription_filename),
            )
            order_id = cursor.lastrowid
            for item in items:
                medicine_id = item["medicine"]["id"]
                cursor.execute(
                    """
                    INSERT INTO order_items (order_id, medicine_id, quantity, unit_price)
                    VALUES (?, ?, ?, ?)
                    """,
                    (order_id, medicine_id, item["quantity"], item["medicine"]["price"]),
                )
                cursor.execute(
                    "UPDATE medicines SET stock_quantity = stock_quantity - ? WHERE id = ?",
                    (item["quantity"], medicine_id),
                )
            connection.commit()
            session.pop("cart", None)
            flash("Order placed successfully.", "success")
            return redirect(url_for("orders.order_detail", order_id=order_id))
        except Exception as error:
            connection.rollback()
            print(f"Order error: {error}")
            flash("Something went wrong while placing your order.", "danger")
        finally:
            cursor.close()
            connection.close()

    return render_template("orders/checkout.html", items=items, total=total)


@orders_bp.route("/orders")
@login_required
def order_history():
    expire_unverified_orders()
    orders = fetch_all(
        """
        SELECT id, total_amount, pickup_location, status, created_at
        FROM orders
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (current_user.id,),
    )
    return render_template("orders/history.html", orders=orders)


@orders_bp.route("/orders/<int:order_id>")
@login_required
def order_detail(order_id):
    expire_unverified_orders()
    owner_filter = "" if current_user.is_admin() else " AND user_id = ?"
    owner_params = (order_id,) if current_user.is_admin() else (order_id, current_user.id)
    order = fetch_one(
        f"""
        SELECT id, total_amount, pickup_location, status, created_at
        FROM orders
        WHERE id = ?{owner_filter}
        """,
        owner_params,
    )
    if order is None:
        flash("Order not found.", "danger")
        return redirect(url_for("orders.order_history"))

    items = fetch_all(
        """
        SELECT medicines.name, order_items.quantity, order_items.unit_price,
               order_items.quantity * order_items.unit_price AS subtotal
        FROM order_items
        JOIN medicines ON medicines.id = order_items.medicine_id
        WHERE order_items.order_id = ?
        ORDER BY medicines.name COLLATE NOCASE
        """,
        (order_id,),
    )
    return render_template("orders/detail.html", order=order, items=items)
