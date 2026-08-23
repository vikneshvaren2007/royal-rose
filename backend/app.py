"""
ROYAL ROSE MILK — Comprehensive Flask Backend Application (v2.1.0)
Handles REST APIs, dynamic product management, customer bookings,
secure order tracking, cancellation flow, dual-email dispatchers,
admin authentication, dashboard aggregation, and static page serving.
"""

import os
import re
import smtplib
import threading
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime
from functools import wraps
from urllib.parse import quote

from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

import database

# Load environment variables explicitly from backend/.env and root .env
_backend_env = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_backend_env):
    load_dotenv(dotenv_path=_backend_env)
load_dotenv()

STATIC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
app = Flask(__name__, template_folder="templates")
CORS(app)

# =========================
# UNIVERSAL CONFIGURATION
# =========================
MAIL_SERVER = (os.getenv("MAIL_SERVER") or os.getenv("EMAIL_HOST") or "smtp.gmail.com").strip()
MAIL_PORT = int(os.getenv("MAIL_PORT") or os.getenv("EMAIL_PORT", 465))
MAIL_USERNAME = (os.getenv("MAIL_USERNAME") or os.getenv("EMAIL_USER") or "vikneshvaren2@gmail.com").strip()
MAIL_PASSWORD = (os.getenv("MAIL_PASSWORD") or os.getenv("EMAIL_PASS") or "bsviciupdnsfzary").strip().replace(" ", "")
MAIL_DEFAULT_SENDER = (os.getenv("MAIL_DEFAULT_SENDER") or MAIL_USERNAME or "vikneshvaren2@gmail.com").strip()
ADMIN_EMAIL = (os.getenv("ADMIN_EMAIL") or os.getenv("ADMIN_MAIL") or "vikneshvaren2@gmail.com").strip()
WHATSAPP_NUMBER = (os.getenv("WHATSAPP_NUMBER") or "919445437069").strip()

# Initialize database schema & initial seeds
database.init_db()


# =========================
# LOGGING HELPER
# =========================
def log_event(category, message):
    """Clean structured logger with timestamp for operational visibility."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    safe_msg = str(message).replace("₹", "Rs.").encode("ascii", "replace").decode("ascii")
    print(f"[{timestamp}] [{category}] {safe_msg}")


# =========================
# ADMIN AUTH DECORATOR
# =========================
def admin_required(f):
    """Decorator to require a valid admin token in headers."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        token = ""
        if auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1].strip()
        if not token:
            token = request.headers.get("X-Admin-Token", "").strip()

        if not token or not database.verify_admin_token(token):
            log_event("AUTH FAILURE", f"Unauthorized admin API access attempt to {request.path}")
            return jsonify({"success": False, "message": "Admin authorization required. Please log in."}), 401
        return f(*args, **kwargs)
    return decorated_function


# =========================
# EMAIL HELPERS
# =========================
def send_email_worker(to_email, subject, html_content, text_content=""):
    """Worker executed in background thread to deliver SMTP email without blocking responses."""
    username = (MAIL_USERNAME or os.getenv("MAIL_USERNAME") or "vikneshvaren2@gmail.com").strip()
    password = (MAIL_PASSWORD or os.getenv("MAIL_PASSWORD") or "bsviciupdnsfzary").strip().replace(" ", "")
    sender = (MAIL_DEFAULT_SENDER or username).strip()

    if not username or not password or not to_email:
        log_event("EMAIL SKIP", f"Credentials missing or empty recipient for '{subject}' to {to_email}")
        return

    try:
        msg = MIMEMultipart("alternative")
        msg["From"] = f"ROYAL ROSE MILK <{sender}>"
        msg["To"] = to_email
        msg["Subject"] = subject

        if text_content:
            msg.attach(MIMEText(text_content, "plain", "utf-8"))
        if html_content:
            msg.attach(MIMEText(html_content, "html", "utf-8"))

        delivered = False
        last_err = None

        # Primary: SMTP_SSL over port 465
        try:
            with smtplib.SMTP_SSL(MAIL_SERVER, 465, timeout=12) as server:
                server.login(username, password)
                server.send_message(msg)
                delivered = True
        except Exception as e1:
            last_err = e1
            log_event("EMAIL RETRY", f"SSL 465 connection note ({e1}). Retrying with STARTTLS 587...")

        # Fallback: SMTP over port 587 with STARTTLS
        if not delivered:
            try:
                with smtplib.SMTP(MAIL_SERVER, 587, timeout=12) as server:
                    server.starttls()
                    server.login(username, password)
                    server.send_message(msg)
                    delivered = True
            except Exception as e2:
                last_err = e2

        if delivered:
            log_event("EMAIL SUCCESS", f"Delivered '{subject}' to {to_email}")
        else:
            log_event("EMAIL ERROR", f"Failed to deliver '{subject}' to {to_email}: {last_err}")

    except Exception as e:
        log_event("EMAIL ERROR", f"Failed to send email to {to_email}: {e}")


def send_email_async(to_email, subject, html_content, text_content=""):
    """Dispatches email sending asynchronously in a background thread."""
    thread = threading.Thread(target=send_email_worker, args=(to_email, subject, html_content, text_content))
    thread.daemon = True
    thread.start()


# =========================
# EMAIL TEMPLATE BUILDERS
# =========================
def build_customer_confirmation_email_html(order):
    """Builds luxury customer booking confirmation email with complete order details."""
    cust = order.get("customer", {})
    items = order.get("items", [])

    items_rows = ""
    for it in items:
        items_rows += f"""
        <tr>
            <td style="padding: 10px 12px; border-bottom: 1px solid #331526; color: #f5f0f3;">{it.get('product_name')}</td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #331526; text-align: center; color: #f5f0f3;">{it.get('quantity')}</td>
            <td style="padding: 10px 12px; border-bottom: 1px solid #331526; text-align: right; color: #ff529a; font-weight: bold;">₹{it.get('subtotal')}</td>
        </tr>
        """

    delivery_pref = order.get('delivery_preference', 'Standard Delivery')
    notes = order.get('notes', '')
    notes_html = f"<p style='color: #ffb8d6; font-size: 13px; margin-top: 10px;'><strong>Special Instructions:</strong> {notes}</p>" if notes else ""

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="margin:0; padding:0; background-color:#0c0409; font-family: 'Helvetica Neue', Arial, sans-serif; color:#f5f0f3;">
        <table width="100%" cellpadding="0" cellspacing="0" style="background-color:#0c0409; padding: 40px 10px;">
            <tr>
                <td align="center">
                    <table width="600" cellpadding="0" cellspacing="0" style="background: linear-gradient(135deg, #180813, #230b1c); border: 1px solid rgba(255, 82, 154, 0.3); border-radius: 16px; overflow: hidden;">
                        <tr>
                            <td style="padding: 30px; text-align: center; background: radial-gradient(circle, #7d0d42 0%, #1a0410 100%);">
                                <h1 style="margin: 0; color: #ffffff; font-size: 28px; letter-spacing: 4px;">♛ ROYAL ROSE MILK</h1>
                                <p style="margin: 5px 0 0 0; color: #ffb8d6; font-size: 12px; letter-spacing: 2px;">BOOKING CONFIRMED</p>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 30px 40px;">
                                <p style="font-size: 16px; color: #ffffff; margin-top: 0;">Dear <strong>{cust.get('name')}</strong>,</p>
                                <p style="font-size: 14px; color: #d0c0c9; line-height: 1.6;">
                                    Your booking has been <strong>successfully confirmed</strong>! Our artisans are preparing your signature Royal Rose Milk with utmost craftsmanship.
                                </p>
                                <div style="background: #11050d; border: 1px dashed #ff529a; border-radius: 8px; padding: 15px; text-align: center; margin: 25px 0;">
                                    <span style="font-size: 12px; color: #a8949f; letter-spacing: 1.5px; display: block;">YOUR UNIQUE BOOKING ID</span>
                                    <strong style="font-size: 24px; color: #ff529a; letter-spacing: 2px;">{order.get('order_id')}</strong>
                                </div>
                                <h3 style="color: #ffb8d6; font-size: 16px; border-bottom: 1px solid #331526; padding-bottom: 8px; margin-top: 25px;">Order Summary</h3>
                                <table width="100%" cellpadding="0" cellspacing="0" style="font-size: 14px; margin-bottom: 20px; border-collapse: collapse;">
                                    <thead>
                                        <tr style="background-color: #260a1e; color: #ffb8d6;">
                                            <th style="padding: 10px 12px; text-align: left;">Product / Variety</th>
                                            <th style="padding: 10px 12px; text-align: center;">Qty</th>
                                            <th style="padding: 10px 12px; text-align: right;">Total</th>
                                        </tr>
                                    </thead>
                                    <tbody>{items_rows}</tbody>
                                </table>
                                <table width="100%" cellpadding="0" cellspacing="0" style="font-size: 14px; margin-top: 15px;">
                                    <tr>
                                        <td style="color: #a8949f; padding: 5px 0;">Subtotal:</td>
                                        <td style="text-align: right; color: #ffffff; padding: 5px 0;">₹{order.get('subtotal')}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #a8949f; padding: 5px 0;">Delivery ({delivery_pref}):</td>
                                        <td style="text-align: right; color: #ffffff; padding: 5px 0;">₹{order.get('delivery_charge')}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #ff529a; font-weight: bold; font-size: 16px; padding: 10px 0 0 0; border-top: 1px solid #331526;">Grand Total:</td>
                                        <td style="text-align: right; color: #ff529a; font-weight: bold; font-size: 18px; padding: 10px 0 0 0; border-top: 1px solid #331526;">₹{order.get('total_amount')}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #a8949f; padding: 5px 0;">Payment Method / Status:</td>
                                        <td style="text-align: right; color: #4ade80; padding: 5px 0; font-weight: bold;">{order.get('payment_method', 'Cash on Delivery')} ({order.get('payment_status', 'PENDING')})</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #a8949f; padding: 5px 0;">Booking Date &amp; Time:</td>
                                        <td style="text-align: right; color: #ffffff; padding: 5px 0;">{order.get('booking_date')}</td>
                                    </tr>
                                    <tr>
                                        <td style="color: #a8949f; padding: 5px 0;">Delivery Address:</td>
                                        <td style="text-align: right; color: #ffffff; padding: 5px 0;">{cust.get('address')}, {cust.get('city')} - {cust.get('pincode')}</td>
                                    </tr>
                                </table>
                                {notes_html}
                                <div style="margin-top: 30px; text-align: center;">
                                    <p style="font-size: 13px; color: #a8949f; line-height: 1.6;">
                                        Track your order anytime using your Booking ID <strong>{order.get('order_id')}</strong> and your email/phone.
                                    </p>
                                </div>
                            </td>
                        </tr>
                        <tr>
                            <td style="padding: 20px; text-align: center; background: #0e030b; border-top: 1px solid #230b1c; font-size: 11px; color: #8a7380;">
                                ROYAL ROSE MILK — Timeless Flavor &amp; Royal Refreshment<br>
                                Tamil Nadu, India • Phone: +91 9445437069
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """


def build_admin_booking_email_html(order):
    """Builds complete admin notification email with all customer and booking details."""
    cust = order.get("customer", {})
    items = order.get("items", [])

    items_rows = ""
    for it in items:
        items_rows += f"""
        <tr>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0;">{it.get('product_name')}</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: center;">{it.get('quantity')}</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: right;">₹{it.get('unit_price')}</td>
            <td style="padding: 8px 10px; border-bottom: 1px solid #e2e8f0; text-align: right; font-weight: bold; color: #8e2346;">₹{it.get('subtotal')}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background: #f4f4f7; padding: 20px; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; background: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.08); border: 1px solid #e2e8f0;">
            <div style="background: #8e2346; color: #ffffff; padding: 20px; text-align: center;">
                <h2 style="margin: 0; font-size: 22px; letter-spacing: 1px;">🚨 NEW BOOKING RECEIVED</h2>
                <p style="margin: 5px 0 0 0; font-size: 14px; opacity: 0.9;">Booking ID: <strong>{order.get('order_id')}</strong></p>
            </div>
            <div style="padding: 25px;">
                <h3 style="color: #8e2346; border-bottom: 2px solid #8e2346; padding-bottom: 5px; margin-top: 0; font-size: 16px;">Customer Information</h3>
                <table width="100%" style="font-size: 14px; margin-bottom: 20px; line-height: 1.6;">
                    <tr><td width="35%"><strong>Customer Name:</strong></td><td>{cust.get('name')}</td></tr>
                    <tr><td><strong>Customer Email:</strong></td><td><a href="mailto:{cust.get('email')}" style="color: #8e2346;">{cust.get('email')}</a></td></tr>
                    <tr><td><strong>Customer Phone:</strong></td><td><a href="tel:{cust.get('phone')}" style="color: #8e2346;">{cust.get('phone')}</a></td></tr>
                    <tr><td><strong>Delivery Address:</strong></td><td>{cust.get('address')}, {cust.get('city')}, {cust.get('state', 'Tamil Nadu')} - {cust.get('pincode')}</td></tr>
                    <tr><td><strong>Delivery Option:</strong></td><td>{order.get('delivery_preference', 'Standard Delivery')}</td></tr>
                    <tr><td><strong>Special Notes:</strong></td><td>{order.get('notes') or 'None'}</td></tr>
                    <tr><td><strong>Date &amp; Time:</strong></td><td>{order.get('booking_date')}</td></tr>
                    <tr><td><strong>Payment Method:</strong></td><td>{order.get('payment_method', 'Cash on Delivery')}</td></tr>
                    <tr><td><strong>Payment Status:</strong></td><td><strong>{order.get('payment_status', 'PENDING')}</strong></td></tr>
                </table>

                <h3 style="color: #8e2346; border-bottom: 2px solid #8e2346; padding-bottom: 5px; font-size: 16px;">Ordered Items</h3>
                <table width="100%" style="font-size: 14px; border-collapse: collapse; margin-bottom: 15px;">
                    <thead>
                        <tr style="background: #fdf2f6; color: #8e2346;">
                            <th style="padding: 8px 10px; text-align: left;">Product</th>
                            <th style="padding: 8px 10px; text-align: center;">Qty</th>
                            <th style="padding: 8px 10px; text-align: right;">Unit Price</th>
                            <th style="padding: 8px 10px; text-align: right;">Subtotal</th>
                        </tr>
                    </thead>
                    <tbody>{items_rows}</tbody>
                </table>

                <div style="text-align: right; font-size: 14px; border-top: 1px solid #e2e8f0; padding-top: 10px;">
                    <p style="margin: 3px 0;">Subtotal: <strong>₹{order.get('subtotal')}</strong></p>
                    <p style="margin: 3px 0;">Delivery Charge: <strong>₹{order.get('delivery_charge')}</strong></p>
                    <p style="margin: 6px 0; font-size: 18px; color: #8e2346;"><strong>Grand Total: ₹{order.get('total_amount')}</strong></p>
                </div>
            </div>
            <div style="background: #f8fafc; padding: 12px; text-align: center; font-size: 12px; color: #64748b; border-top: 1px solid #e2e8f0;">
                Royal Rose Milk Automated Store Notification
            </div>
        </div>
    </body>
    </html>
    """


def build_cancellation_email_html(order, is_admin=False):
    """Builds customer/admin cancellation notification email with complete details."""
    cust = order.get("customer", {})
    items = order.get("items", [])
    recipient_title = "ORDER / BOOKING CANCELLED" if not is_admin else "🚨 BOOKING CANCELLED"

    items_rows = ""
    for it in items:
        items_rows += f"""
        <tr>
            <td style="padding: 8px; border-bottom: 1px solid #44112c; color: #f5f0f3;">{it.get('product_name')}</td>
            <td style="padding: 8px; border-bottom: 1px solid #44112c; text-align: center; color: #f5f0f3;">{it.get('quantity')}</td>
            <td style="padding: 8px; border-bottom: 1px solid #44112c; text-align: right; color: #f87171;">₹{it.get('subtotal')}</td>
        </tr>
        """

    cancelled_by_label = order.get('cancelled_by', 'CUSTOMER')
    pay_status = order.get('payment_status', 'PENDING')
    refund_status = "Cash on Delivery (No payment was collected)" if "cash" in str(order.get('payment_method', '')).lower() else f"Payment Status: {pay_status} (Refund under review)"

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="utf-8"></head>
    <body style="font-family: Arial, sans-serif; background: #1a0410; padding: 20px; color: #f5f0f3; margin: 0;">
        <div style="max-width: 600px; margin: 0 auto; background: #230b1c; border: 1px solid #ef4444; border-radius: 12px; padding: 30px; box-shadow: 0 10px 30px rgba(0,0,0,0.5);">
            <div style="text-align: center; border-bottom: 1px solid #44112c; padding-bottom: 20px;">
                <h2 style="color: #ef4444; margin: 0; font-size: 22px; letter-spacing: 1px;">{recipient_title}</h2>
                <p style="color: #ffb8d6; margin: 6px 0 0 0; font-size: 14px;">Booking ID: <strong>{order.get('order_id')}</strong></p>
            </div>
            <div style="padding: 20px 0; font-size: 14px; line-height: 1.7;">
                <p style="margin-top: 0;">
                    Booking <strong>{order.get('order_id')}</strong> for <strong>{cust.get('name')}</strong> ({cust.get('email')}, {cust.get('phone')}) has been marked as <strong style="color: #ef4444;">CANCELLED</strong>.
                </p>
                <table width="100%" style="font-size: 13px; margin-bottom: 15px;">
                    <tr><td width="40%" style="color: #a8949f;"><strong>Original Booking Date:</strong></td><td>{order.get('booking_date') or order.get('created_at')}</td></tr>
                    <tr><td style="color: #a8949f;"><strong>Cancellation Date/Time:</strong></td><td>{order.get('cancelled_at')}</td></tr>
                    <tr><td style="color: #a8949f;"><strong>Cancelled By:</strong></td><td>{cancelled_by_label}</td></tr>
                    <tr><td style="color: #a8949f;"><strong>Cancellation Reason:</strong></td><td>{order.get('cancellation_reason') or 'Customer requested cancellation'}</td></tr>
                    <tr><td style="color: #a8949f;"><strong>Total Amount:</strong></td><td style="font-weight: bold; color: #ff529a;">₹{order.get('total_amount')}</td></tr>
                    <tr><td style="color: #a8949f;"><strong>Payment / Refund:</strong></td><td>{refund_status}</td></tr>
                </table>

                {f'''
                <h4 style="color: #ffb8d6; margin-bottom: 8px; border-bottom: 1px solid #44112c; padding-bottom: 4px;">Cancelled Items</h4>
                <table width="100%" style="font-size: 13px; border-collapse: collapse; margin-bottom: 15px;">
                    <thead>
                        <tr style="background: #1a0410; color: #ffb8d6;">
                            <th style="padding: 6px 8px; text-align: left;">Product</th>
                            <th style="padding: 6px 8px; text-align: center;">Qty</th>
                            <th style="padding: 6px 8px; text-align: right;">Amount</th>
                        </tr>
                    </thead>
                    <tbody>{items_rows}</tbody>
                </table>
                ''' if items_rows else ''}
            </div>
            <div style="text-align: center; font-size: 12px; color: #a8949f; border-top: 1px solid #44112c; padding-top: 15px;">
                ROYAL ROSE MILK System Notification • Support: +91 9445437069
            </div>
        </div>
    </body>
    </html>
    """


def build_contact_email_html(name, email, phone, message):
    """Builds contact message notification for admin."""
    return f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; background: #fafafa; border-radius: 8px; max-width: 500px; border: 1px solid #eee;">
        <h3 style="color: #8e2346; margin-top: 0;">New Contact Inquiry</h3>
        <p><strong>Name:</strong> {name}</p>
        <p><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
        <p><strong>Phone:</strong> {phone or 'Not provided'}</p>
        <p><strong>Message:</strong></p>
        <blockquote style="background: #fff; padding: 12px; border-left: 3px solid #8e2346; margin: 0;">
            {message}
        </blockquote>
    </div>
    """


# =========================
# SYSTEM & HEALTH APIS
# =========================
@app.route("/api/health")
def api_health():
    """Health check endpoint confirming service status and database connectivity."""
    try:
        with database.get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1;")
            db_status = "connected"
    except Exception as e:
        log_event("DATABASE ERROR", f"Health check DB error: {e}")
        db_status = f"error: {e}"

    return jsonify({
        "status": "ok",
        "service": "ROYAL ROSE MILK API",
        "database": db_status,
        "timestamp": datetime.now().isoformat(),
        "version": "2.0.0"
    }), 200


@app.route("/")
def home():
    """Serves the main customer storefront."""
    if request.args.get("json") == "1" or (request.accept_mimetypes.accept_json and not request.accept_mimetypes.accept_html):
        return jsonify({
            "status": "ok",
            "service": "ROYAL ROSE MILK API",
            "database": "connected",
            "timestamp": datetime.now().isoformat()
        })
    return send_from_directory(STATIC_DIR, "index.html")


# =========================
# PUBLIC PRODUCT & SETTINGS APIS
# =========================
@app.route("/api/products", methods=["GET"])
def get_products():
    """Returns all active & visible products for the customer storefront."""
    try:
        products = database.get_visible_products()
        return jsonify({"success": True, "products": products}), 200
    except Exception as e:
        log_event("DATABASE ERROR", f"Failed to retrieve visible products: {e}")
        return jsonify({"success": False, "message": "Unable to load products."}), 500


@app.route("/api/settings", methods=["GET"])
def get_settings():
    """Returns public shop settings."""
    try:
        settings = database.get_shop_settings()
        return jsonify({"success": True, "settings": settings}), 200
    except Exception as e:
        log_event("DATABASE ERROR", f"Failed to retrieve settings: {e}")
        return jsonify({"success": False, "message": "Unable to load settings."}), 500


# =========================
# BOOKING & ORDER FLOW
# =========================
@app.route("/book", methods=["POST"])
@app.route("/api/book", methods=["POST"])
def book_order():
    """
    Handles new customer booking:
    1. Validates customer and products input.
    2. Validates product availability (rejects sold-out items).
    3. Persists to SQLite DB transactionally.
    4. Generates unique Order ID.
    5. Dispatches dual async confirmation emails (Customer + Admin).
    6. Returns confirmed order details.
    """
    try:
        data = request.get_json(force=True, silent=True)
        if not data:
            return jsonify({"success": False, "message": "No booking data received."}), 400

        customer = data.get("customer", {})
        products = data.get("products", [])

        # Validate Customer Information
        name = customer.get("name", "").strip()
        email = customer.get("email", "").strip()
        phone = customer.get("phone", "").strip()
        address = customer.get("address", "").strip()
        city = customer.get("city", "").strip()
        pincode = customer.get("pincode", "").strip()
        notes = customer.get("notes", "").strip()
        delivery_pref = data.get("delivery", "Standard Delivery")

        if not name:
            return jsonify({"success": False, "message": "Please enter your name."}), 400

        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not email or not re.match(email_regex, email):
            return jsonify({"success": False, "message": "Please provide a valid email address."}), 400

        phone_clean = re.sub(r"\D", "", phone)
        if not phone_clean or len(phone_clean) < 10:
            return jsonify({"success": False, "message": "Please enter a valid 10-digit phone number."}), 400

        if not address:
            return jsonify({"success": False, "message": "Please enter your delivery address."}), 400

        if not city:
            return jsonify({"success": False, "message": "Please enter your city."}), 400

        if not products or not isinstance(products, list) or len(products) == 0:
            return jsonify({"success": False, "message": "Your cart is empty. Please select at least one item."}), 400

        log_event("BOOKING RECEIVED", f"New booking request from {name} ({email}, {phone})")

        # Save booking transactionally
        try:
            order_data = database.save_booking(
                customer_data={
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "address": address,
                    "city": city,
                    "pincode": pincode
                },
                products_data=products,
                delivery_preference=delivery_pref,
                notes=notes
            )
        except ValueError as ve:
            log_event("BOOKING REJECTED", f"Validation error for {name}: {ve}")
            return jsonify({"success": False, "message": str(ve)}), 400

        order_id = order_data["order_id"]
        log_event("DATABASE SAVE", f"Order #{order_id} successfully persisted in database.")

        # Generate WhatsApp support URL
        wa_text = f"Hello Royal Rose Milk! My booking is confirmed (Order ID: {order_id}) for Total: Rs.{order_data['total_amount']}."
        whatsapp_url = f"https://wa.me/{WHATSAPP_NUMBER}?text={quote(wa_text)}"
        order_data["whatsapp_url"] = whatsapp_url

        # Dispatch async customer confirmation email
        cust_html = build_customer_confirmation_email_html(order_data)
        send_email_async(
            to_email=email,
            subject=f"♛ Booking Confirmed — Order #{order_id} | ROYAL ROSE MILK",
            html_content=cust_html,
            text_content=f"Thank you for your order {order_id}. Total: Rs.{order_data['total_amount']}."
        )
        log_event("CONFIRMATION EMAIL (CUSTOMER)", f"Dispatched booking confirmation email to {email}")

        # Dispatch async admin notification email
        admin_html = build_admin_booking_email_html(order_data)
        send_email_async(
            to_email=ADMIN_EMAIL,
            subject=f"🚨 New Booking #{order_id} from {name} (Rs.{order_data['total_amount']})",
            html_content=admin_html,
            text_content=f"New booking {order_id} received from {name} ({phone}, {email}). Total: Rs.{order_data['total_amount']}."
        )
        log_event("CONFIRMATION EMAIL (ADMIN)", f"Dispatched booking alert to admin {ADMIN_EMAIL}")

        return jsonify({
            "success": True,
            "message": "Booking confirmed successfully!",
            "order_id": order_id,
            "order": order_data,
            "whatsapp_url": whatsapp_url
        }), 200

    except Exception as e:
        log_event("DATABASE ERROR", f"Booking processing error: {e}")
        return jsonify({"success": False, "message": "Unable to complete booking at this time. Please try again."}), 500


# =========================
# ORDER TRACKING & CANCELLATION
# =========================
@app.route("/api/track", methods=["POST"])
def track_order():
    """Look up order by Order ID + Email or Phone."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        order_id = str(data.get("order_id") or data.get("orderId") or data.get("id") or "").strip()
        verification = str(data.get("verification") or data.get("verify") or data.get("email") or data.get("phone") or "").strip()

        if not order_id or not verification:
            return jsonify({"success": False, "message": "Both Order ID and Email/Phone are required."}), 400

        order = database.get_order_by_id_and_verification(order_id, verification)
        if not order:
            return jsonify({"success": False, "message": "Order not found. Please check your Order ID and Email/Phone number."}), 404

        return jsonify({"success": True, "order": order}), 200

    except Exception as e:
        log_event("TRACK ERROR", f"Error tracking order: {e}")
        return jsonify({"success": False, "message": "Error looking up order status."}), 500


@app.route("/api/cancel", methods=["POST"])
@app.route("/api/orders/<order_id>/cancel", methods=["POST"])
def cancel_order_endpoint(order_id=None):
    """Cancel order with security verification and dispatch dual cancellation emails."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        oid = str(order_id or data.get("order_id") or data.get("orderId") or "").strip()
        verification = str(data.get("verification") or data.get("verify") or data.get("email") or data.get("phone") or "").strip()
        reason = str(data.get("reason", "Customer requested cancellation")).strip()

        cancelled_by = str(data.get("cancelled_by", "CUSTOMER")).strip().upper()

        if not oid:
            return jsonify({"success": False, "message": "Order ID is required."}), 400

        cancelled_order, msg = database.cancel_order(oid, verification if verification else None, reason, cancelled_by=cancelled_by)
        if not cancelled_order:
            return jsonify({"success": False, "message": msg}), 400

        log_event("CANCELLATION RECEIVED", f"Order #{oid} cancelled by {cancelled_by}. Reason: {reason}")

        # Dispatch async cancellation emails
        cust_email = cancelled_order.get("customer", {}).get("email")
        if cust_email:
            send_email_async(
                to_email=cust_email,
                subject=f"⚠️ Order #{oid} Cancelled — ROYAL ROSE MILK",
                html_content=build_cancellation_email_html(cancelled_order, is_admin=False),
                text_content=f"Your order {oid} has been cancelled."
            )
            log_event("CANCELLATION EMAIL (CUSTOMER)", f"Dispatched cancellation email to {cust_email}")

        send_email_async(
            to_email=ADMIN_EMAIL,
            subject=f"⚠️ Order #{oid} Cancelled by Customer",
            html_content=build_cancellation_email_html(cancelled_order, is_admin=True),
            text_content=f"Order {oid} was cancelled by the customer."
        )
        log_event("CANCELLATION EMAIL (ADMIN)", f"Dispatched cancellation alert to admin {ADMIN_EMAIL}")

        return jsonify({
            "success": True,
            "message": "Order successfully cancelled.",
            "order": cancelled_order
        }), 200

    except Exception as e:
        log_event("CANCEL ERROR", f"Cancellation error: {e}")
        return jsonify({"success": False, "message": "Server error while processing cancellation."}), 500


# =========================
# CONTACT FORM
# =========================
@app.route("/api/contact", methods=["POST"])
def contact_submit():
    """Handles customer contact messages."""
    try:
        data = request.get_json(force=True, silent=True) or {}
        name = data.get("name", "").strip()
        email = data.get("email", "").strip()
        phone = data.get("phone", "").strip()
        message = data.get("message", "").strip()

        if not name:
            return jsonify({"success": False, "message": "Please enter your name."}), 400

        email_regex = r"^[\w\.-]+@[\w\.-]+\.\w+$"
        if not email or not re.match(email_regex, email):
            return jsonify({"success": False, "message": "Please provide a valid email address."}), 400

        if not message:
            return jsonify({"success": False, "message": "Please enter your message."}), 400

        msg_id = database.save_contact_message(name, email, phone, message)
        log_event("CONTACT INQUIRY", f"Inquiry #{msg_id} from {name} ({email})")

        # Notify admin asynchronously
        contact_html = build_contact_email_html(name, email, phone, message)
        send_email_async(
            to_email=ADMIN_EMAIL,
            subject=f"✉️ Contact Message from {name}",
            html_content=contact_html,
            text_content=f"Inquiry from {name} ({email}, {phone}):\n\n{message}"
        )

        return jsonify({
            "success": True,
            "message": "Thank you! Your message has been sent successfully. We will get back to you shortly.",
            "id": msg_id
        }), 200

    except Exception as e:
        log_event("CONTACT ERROR", f"Contact error: {e}")
        return jsonify({"success": False, "message": "Unable to send message at this moment. Please try again."}), 500


# =========================
# ADMIN AUTHENTICATION
# =========================
@app.route("/api/admin/login", methods=["POST"])
def admin_login():
    """Admin login endpoint."""
    data = request.get_json(force=True, silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "").strip()

    if not username or not password:
        return jsonify({"success": False, "message": "Username and password required."}), 400

    success, result = database.verify_admin_credentials(username, password)
    if success:
        log_event("AUTH SUCCESS", f"Admin user '{username}' logged in successfully.")
        return jsonify({
            "success": True,
            "message": "Login successful.",
            "token": result,
            "username": username
        }), 200

    log_event("AUTH FAILURE", f"Failed admin login attempt for username '{username}'")
    return jsonify({"success": False, "message": result}), 401


@app.route("/api/admin/verify-token", methods=["GET"])
def admin_verify_token():
    """Verifies whether current admin session token is valid."""
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1].strip()
    if not token:
        token = request.headers.get("X-Admin-Token", "").strip()

    if database.verify_admin_token(token):
        return jsonify({"success": True, "valid": True}), 200
    return jsonify({"success": False, "valid": False}), 401


@app.route("/api/admin/logout", methods=["POST"])
def admin_logout():
    """Admin logout endpoint."""
    auth_header = request.headers.get("Authorization", "")
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1].strip()
    if not token:
        token = request.headers.get("X-Admin-Token", "").strip()

    database.invalidate_admin_token(token)
    log_event("AUTH LOGOUT", "Admin logged out successfully.")
    return jsonify({"success": True, "message": "Logged out."}), 200


# =========================
# ADMIN DASHBOARD & ORDERS
# =========================
@app.route("/admin")
@app.route("/admin.html")
@app.route("/admin/login")
@app.route("/admin/dashboard")
def admin_page():
    """Renders the luxury Admin Panel."""
    data = database.get_admin_dashboard_data()
    return render_template("admin.html", orders=data["orders"], products=data["products"], customers=data["customers"], messages=data["messages"], stats=data["stats"], settings=data["settings"])


@app.route("/api/admin/dashboard", methods=["GET"])
@app.route("/api/admin/orders", methods=["GET"])
@admin_required
def admin_dashboard_api():
    """Returns complete admin aggregation (stats, orders, products, customers, inquiries, settings)."""
    data = database.get_admin_dashboard_data()
    return jsonify({"success": True, "data": data}), 200


@app.route("/api/admin/orders/<order_id>", methods=["GET"])
@admin_required
def admin_get_single_order(order_id):
    """Retrieve complete 360-degree details for an individual order."""
    order = database.get_order_by_id(order_id)
    if not order:
        return jsonify({"success": False, "message": f"Order #{order_id} not found."}), 404
    return jsonify({"success": True, "order": order}), 200


@app.route("/api/admin/order-status", methods=["POST"])
@admin_required
def admin_update_order_status():
    """Updates order status and sends cancellation emails if marked CANCELLED."""
    data = request.get_json(force=True, silent=True) or {}
    order_id = data.get("order_id", "").strip()
    status = data.get("status", "").strip().upper()
    reason = data.get("reason", "Cancelled by store administrator").strip()

    if not order_id or not status:
        return jsonify({"success": False, "message": "Order ID and status required."}), 400

    success, msg = database.update_order_status(order_id, status, cancelled_by="ADMIN", reason=reason)
    if not success:
        return jsonify({"success": False, "message": msg}), 400

    log_event("ORDER STATUS", f"Order #{order_id} status updated to {status} by admin.")

    # If status is CANCELLED, dispatch dual cancellation emails
    if status == "CANCELLED":
        order_obj = database.get_order_by_id(order_id)
        if order_obj:
            cust_email = order_obj.get("customer", {}).get("email")
            if cust_email:
                send_email_async(
                    to_email=cust_email,
                    subject=f"⚠️ Order #{order_id} Cancelled — ROYAL ROSE MILK",
                    html_content=build_cancellation_email_html(order_obj, is_admin=False),
                    text_content=f"Your order {order_id} has been cancelled by store administrator."
                )
                log_event("CANCELLATION EMAIL (CUSTOMER)", f"Dispatched cancellation email to {cust_email}")

            send_email_async(
                to_email=ADMIN_EMAIL,
                subject=f"⚠️ Order #{order_id} Cancelled by Admin",
                html_content=build_cancellation_email_html(order_obj, is_admin=True),
                text_content=f"Order {order_id} was cancelled by admin. Reason: {reason}"
            )
            log_event("CANCELLATION EMAIL (ADMIN)", f"Dispatched cancellation alert to admin {ADMIN_EMAIL}")

    return jsonify({"success": True, "message": msg}), 200


@app.route("/api/admin/payment-status", methods=["POST"])
@admin_required
def admin_update_payment_status():
    """Update payment status for an order (PENDING, PAID, FAILED, REFUNDED)."""
    data = request.get_json(force=True, silent=True) or {}
    order_id = data.get("order_id", "").strip()
    pay_status = data.get("payment_status", "").strip().upper()

    if not order_id or not pay_status:
        return jsonify({"success": False, "message": "Order ID and payment status required."}), 400

    success, msg = database.update_order_payment_status(order_id, pay_status)
    if not success:
        return jsonify({"success": False, "message": msg}), 400

    log_event("PAYMENT STATUS", f"Order #{order_id} payment status updated to {pay_status} by admin.")
    return jsonify({"success": True, "message": msg}), 200


# =========================
# ADMIN CUSTOMER MANAGEMENT
# =========================
@app.route("/api/admin/customers", methods=["GET"])
@admin_required
def admin_get_customers():
    """Retrieve all customers with order metrics."""
    customers = database.get_all_customers_admin()
    return jsonify({"success": True, "customers": customers}), 200


@app.route("/api/admin/customers/<int:cust_id>/orders", methods=["GET"])
@admin_required
def admin_get_customer_orders(cust_id):
    """Retrieve order history for a specific customer."""
    orders = database.get_customer_orders_by_id(cust_id)
    return jsonify({"success": True, "orders": orders}), 200


# =========================
# ADMIN PRODUCT MANAGEMENT
# =========================
@app.route("/api/admin/products", methods=["GET"])
@admin_required
def admin_get_products():
    """Returns all products including hidden ones."""
    products = database.get_all_products_admin()
    return jsonify({"success": True, "products": products}), 200


@app.route("/api/admin/products", methods=["POST"])
@admin_required
def admin_create_product():
    """Create a new product."""
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    price = data.get("price", 0)
    description = data.get("description", "").strip()
    image = data.get("image", "images/Royal Rose Milk.jpg").strip()
    ingredients = data.get("ingredients", "").strip()
    category = data.get("category", "Rose Milk").strip()
    badge = data.get("badge", "").strip()

    if not name:
        return jsonify({"success": False, "message": "Product name is required."}), 400
    try:
        price_num = float(price)
        if price_num <= 0:
            return jsonify({"success": False, "message": "Price must be greater than 0."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid price."}), 400

    new_id = database.add_product(
        name=name,
        description=description,
        price=price_num,
        image=image,
        ingredients=ingredients,
        category=category,
        badge=badge,
        available=int(data.get("available", 1)),
        sold_out=int(data.get("sold_out", 0)),
        visible=int(data.get("visible", 1)),
        featured=int(data.get("featured", 0))
    )
    log_event("PRODUCT CREATED", f"Product '{name}' (ID: {new_id}, ₹{price_num}) created by admin.")

    return jsonify({"success": True, "message": f"Product '{name}' created successfully.", "id": new_id}), 201


@app.route("/api/admin/products/<int:prod_id>", methods=["POST", "PUT"])
@admin_required
def admin_update_product(prod_id):
    """Edit an existing product."""
    data = request.get_json(force=True, silent=True) or {}
    name = data.get("name", "").strip()
    price = data.get("price", 0)
    description = data.get("description", "").strip()
    image = data.get("image", None)
    ingredients = data.get("ingredients", "").strip()
    category = data.get("category", "Rose Milk").strip()
    badge = data.get("badge", "").strip()

    if not name:
        return jsonify({"success": False, "message": "Product name is required."}), 400
    try:
        price_num = float(price)
        if price_num <= 0:
            return jsonify({"success": False, "message": "Price must be greater than 0."}), 400
    except (ValueError, TypeError):
        return jsonify({"success": False, "message": "Invalid price."}), 400

    success = database.update_product(
        product_id=prod_id,
        name=name,
        description=description,
        price=price_num,
        image=image,
        ingredients=ingredients,
        category=category,
        badge=badge,
        available=int(data.get("available", 1)),
        sold_out=int(data.get("sold_out", 0)),
        visible=int(data.get("visible", 1)),
        featured=int(data.get("featured", 0))
    )

    if success:
        log_event("PRODUCT UPDATED", f"Product ID {prod_id} ('{name}', ₹{price_num}) updated by admin.")
        return jsonify({"success": True, "message": f"Product '{name}' updated successfully."}), 200
    return jsonify({"success": False, "message": "Product not found or update failed."}), 404


@app.route("/api/admin/products/<int:prod_id>/toggle-sold-out", methods=["POST"])
@admin_required
def admin_toggle_sold_out(prod_id):
    """Toggles product sold-out status."""
    success, result = database.toggle_product_sold_out(prod_id)
    if success:
        label = "SOLD OUT" if result == 1 else "AVAILABLE"
        log_event("PRODUCT STATUS", f"Product ID {prod_id} sold-out set to {label}.")
        return jsonify({"success": True, "message": f"Product status set to {label}.", "sold_out": result}), 200
    return jsonify({"success": False, "message": result}), 404


@app.route("/api/admin/products/<int:prod_id>/toggle-visibility", methods=["POST"])
@admin_required
def admin_toggle_visibility(prod_id):
    """Toggles product visibility status."""
    success, result = database.toggle_product_visibility(prod_id)
    if success:
        label = "VISIBLE" if result == 1 else "HIDDEN"
        log_event("PRODUCT VISIBILITY", f"Product ID {prod_id} visibility set to {label}.")
        return jsonify({"success": True, "message": f"Product visibility set to {label}.", "visible": result}), 200
    return jsonify({"success": False, "message": result}), 404


@app.route("/api/admin/products/<int:prod_id>", methods=["DELETE"])
@admin_required
def admin_delete_product(prod_id):
    """Deletes a product."""
    success = database.delete_product(prod_id)
    if success:
        log_event("PRODUCT DELETED", f"Product ID {prod_id} deleted by admin.")
        return jsonify({"success": True, "message": "Product deleted successfully."}), 200
    return jsonify({"success": False, "message": "Product not found."}), 404


@app.route("/api/admin/settings", methods=["POST"])
@admin_required
def admin_update_settings():
    """Updates shop settings."""
    data = request.get_json(force=True, silent=True) or {}
    database.update_shop_settings(data)
    log_event("SETTINGS UPDATED", "Shop settings updated by admin.")
    return jsonify({"success": True, "message": "Shop settings updated successfully."}), 200


# =========================
# STATIC FILE & PAGE SERVING
# =========================
@app.route("/")
@app.route("/index.html")
def serve_index():
    return send_from_directory(STATIC_DIR, "index.html")

@app.route("/shop.html")
def serve_shop():
    return send_from_directory(STATIC_DIR, "shop.html")

@app.route("/cart.html")
def serve_cart():
    return send_from_directory(STATIC_DIR, "cart.html")

@app.route("/booking.html")
def serve_booking():
    return send_from_directory(STATIC_DIR, "booking.html")

@app.route("/booking-success.html")
def serve_booking_success():
    return send_from_directory(STATIC_DIR, "booking-success.html")

@app.route("/track.html")
def serve_track():
    return send_from_directory(STATIC_DIR, "track.html")

@app.route("/contact.html")
def serve_contact():
    return send_from_directory(STATIC_DIR, "contact.html")

@app.route("/<path:filename>")
def serve_page_or_static(filename):
    return send_from_directory(STATIC_DIR, filename)


# =========================
# RUN SERVER
# =========================
if __name__ == "__main__":
    print("[ROYAL ROSE MILK] Starting Flask Backend on http://127.0.0.1:5000 ...")
    app.run(host="0.0.0.0", port=5000, debug=True)