import os
import smtplib
from email.message import EmailMessage

from flask import current_app

def send_email(recipient, subject, body):
    if not recipient:
        return False
    smtp_host = current_app.config.get("SMTP_HOST") or os.environ.get("SMTP_HOST", "smtp.gmail.com")
    try:
        smtp_port = int(current_app.config.get("SMTP_PORT") or os.environ.get("SMTP_PORT", "587"))
    except ValueError:
        current_app.logger.error("Invalid SMTP_PORT configuration.")
        return False
    smtp_username = current_app.config.get("SMTP_USERNAME") or os.environ.get("SMTP_USERNAME")
    smtp_password = current_app.config.get("SMTP_PASSWORD") or os.environ.get("SMTP_PASSWORD")
    sender = current_app.config.get("MAIL_FROM") or os.environ.get("MAIL_FROM") or smtp_username
    if not smtp_host or not smtp_username or not smtp_password or not sender:
        current_app.logger.warning("Email skipped: Gmail SMTP_USERNAME, SMTP_PASSWORD, and MAIL_FROM are required.")
        return False

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = recipient
    message.set_content(body)
    try:
        use_ssl = current_app.config.get("SMTP_USE_SSL", os.environ.get("SMTP_USE_SSL", "false").lower() == "true")
        smtp_class = smtplib.SMTP_SSL if use_ssl else smtplib.SMTP
        with smtp_class(smtp_host, smtp_port, timeout=10) as server:
            if not use_ssl and current_app.config.get("SMTP_USE_TLS", os.environ.get("SMTP_USE_TLS", "true").lower() == "true"):
                server.starttls()
            if smtp_username and smtp_password:
                server.login(smtp_username, smtp_password)
            server.send_message(message)
        return True
    except (OSError, smtplib.SMTPException) as error:
        current_app.logger.error("Could not send email: %s", error)
        return False

def send_order_status_email(order, status):
    status_label = status.replace("_", " ").title()
    return send_email(
        order.get("contact_email") or order.get("customer_email"),
        f"PharmaCare order #{order['id']} {status_label.lower()}",
        f"Hello {order.get('customer_name', 'Customer')},\n\n"
        f"Your PharmaCare order #{order['id']} has been {status_label.lower()}.\n\n"
        "Thank you for shopping with PharmaCare.",
    )

def send_registration_otp(email, otp):
    return send_email(
        email,
        "Your PharmaCare verification code",
        f"Your PharmaCare verification code is: {otp}\n\n"
        "This code expires in 10 minutes. If you did not request this, ignore this email.",
    )