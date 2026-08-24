import os
import re
import sqlite3
import hashlib
import secrets
from contextlib import contextmanager
from datetime import datetime, timezone, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Indian Standard Time (IST) Timezone Helper (UTC+05:30)
try:
    from zoneinfo import ZoneInfo
    IST = ZoneInfo("Asia/Kolkata")
except Exception:
    IST = timezone(timedelta(hours=5, minutes=30))

def get_ist_now():
    """Returns the current datetime in Indian Standard Time (IST)."""
    return datetime.now(IST)

# Load environment variables from backend/.env or root .env
_backend_env = os.path.join(os.path.dirname(__file__), ".env")
if os.path.exists(_backend_env):
    load_dotenv(dotenv_path=_backend_env)
load_dotenv()

DB_PATH = os.path.join(os.path.dirname(__file__), "royal_rose.db")

# In-memory admin session storage (token -> {username, created_at})
ADMIN_SESSIONS = {}


@contextmanager
def get_db():
    """
    Create and return a database connection with Row factory, foreign keys,
    WAL journal mode, busy timeout, and reliable connection closing.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Initialize database tables, foreign keys, indexes, migrations, and seeds."""
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Customers Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT NOT NULL,
                address TEXT NOT NULL,
                city TEXT NOT NULL,
                state TEXT DEFAULT 'Tamil Nadu',
                pincode TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 2. Products Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                price REAL NOT NULL,
                image TEXT,
                ingredients TEXT,
                category TEXT DEFAULT 'Rose Milk',
                badge TEXT DEFAULT '',
                available INTEGER DEFAULT 1,
                sold_out INTEGER DEFAULT 0,
                visible INTEGER DEFAULT 1,
                featured INTEGER DEFAULT 0,
                rating REAL DEFAULT 4.9,
                reviews_count INTEGER DEFAULT 120,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 3. Orders Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT UNIQUE NOT NULL,
                customer_id INTEGER NOT NULL,
                subtotal REAL NOT NULL,
                delivery_charge REAL NOT NULL DEFAULT 0,
                total_amount REAL NOT NULL,
                delivery_preference TEXT DEFAULT 'Standard Delivery',
                payment_method TEXT DEFAULT 'Cash on Delivery',
                payment_status TEXT DEFAULT 'PENDING',
                order_status TEXT DEFAULT 'CONFIRMED',
                notes TEXT,
                booking_date TEXT,
                cancellation_reason TEXT,
                cancelled_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                cancelled_at TIMESTAMP NULL,
                FOREIGN KEY (customer_id) REFERENCES customers(id) ON DELETE RESTRICT
            );
        """)

        # 4. Order Items Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS order_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id TEXT NOT NULL,
                product_id INTEGER NULL,
                product_name TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                unit_price REAL NOT NULL,
                subtotal REAL NOT NULL,
                FOREIGN KEY (order_id) REFERENCES orders(order_id) ON DELETE CASCADE
            );
        """)

        # Safe Schema Migrations for Existing Databases
        cursor.execute("PRAGMA table_info(order_items);")
        oi_cols = [c["name"] for c in cursor.fetchall()]
        if "product_id" not in oi_cols:
            cursor.execute("ALTER TABLE order_items ADD COLUMN product_id INTEGER NULL;")

        cursor.execute("PRAGMA table_info(customers);")
        c_cols = [c["name"] for c in cursor.fetchall()]
        if "state" not in c_cols:
            cursor.execute("ALTER TABLE customers ADD COLUMN state TEXT DEFAULT 'Tamil Nadu';")

        cursor.execute("PRAGMA table_info(orders);")
        o_cols = [c["name"] for c in cursor.fetchall()]
        if "cancellation_reason" not in o_cols:
            cursor.execute("ALTER TABLE orders ADD COLUMN cancellation_reason TEXT NULL;")
        if "cancelled_by" not in o_cols:
            cursor.execute("ALTER TABLE orders ADD COLUMN cancelled_by TEXT NULL;")
        if "payment_method" not in o_cols:
            cursor.execute("ALTER TABLE orders ADD COLUMN payment_method TEXT DEFAULT 'Cash on Delivery';")
        if "payment_status" not in o_cols:
            cursor.execute("ALTER TABLE orders ADD COLUMN payment_status TEXT DEFAULT 'PENDING';")

        # 5. Contact Messages Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                phone TEXT,
                message TEXT NOT NULL,
                status TEXT DEFAULT 'UNREAD',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 6. Admin Users Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 7. Shop Settings Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS shop_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # 8. Newsletter Subscribers Table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS newsletter_subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_order_id ON orders(order_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_orders_customer_id ON orders(customer_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_email ON customers(email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_customers_phone ON customers(phone);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_order_items_order_id ON order_items(order_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_visible ON products(visible);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_products_sold_out ON products(sold_out);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_newsletter_email ON newsletter_subscribers(email);")

        # SEED 1: Products
        cursor.execute("SELECT COUNT(*) AS cnt FROM products;")
        if cursor.fetchone()["cnt"] == 0:
            seed_products = [
                # CLASSIC COLLECTION
                ("Royal Rose Classic", "Smooth, chilled velvet whole milk infused with authentic Kannauj Damask rose extract.", 149.0, "images/Classic Rose Milk.jpg", "Whole Milk, Damask Rose Extract, Cane Sugar, Cardamom", "Classic Collection", "BESTSELLER", 1, 0, 1, 1, 4.9, 154),
                ("Royal Rose Signature", "Our flagship magnum opus. Concentrated damask rose absolute folded into rich whole cream with green cardamom.", 199.0, "images/Royal Rose Milk.jpg", "A2 Cream, Pure Rose Absolute, Green Cardamom, Rock Sugar", "Classic Collection", "ROYAL FLAGSHIP", 1, 0, 1, 1, 5.0, 230),
                ("Strawberry Rose Bliss", "Sun-ripened hill strawberries pureed into fragrant rose milk for a vibrant sweet-tart balance.", 169.0, "images/strawberry-rose.jpg", "Natural Strawberry Pulp, Rose Milk, Chia Seeds, Raw Honey", "Classic Collection", "POPULAR CHOICE", 1, 0, 1, 1, 4.8, 118),
                ("Rose Cardamom Royale", "Fragrant green cardamom crushed with sun-dried damask rose petals in pure whole milk.", 179.0, "images/cardamom-rose-milk.jpg", "Pure Whole Milk, Green Cardamom, Damask Rose Syrup, Pistachio Bits", "Classic Collection", "TRADITIONAL SPECIAL", 1, 0, 1, 1, 4.9, 142),
                
                # SPECIALITY BLENDS
                ("Royal Kashmiri Saffron Elixir", "Pure Grade-A Kashmiri saffron threads gently steeped in aromatic chilled Damask rose cream.", 249.0, "images/saffron-rose-milk.jpg", "Kashmiri Mogra Saffron, Whole Cream Milk, Rose Absolute, Almond Essence", "Speciality Blends", "GOLD EDITION", 1, 0, 1, 1, 5.0, 310),
                ("Royal Pistachio Velvet", "Crushed roasted Iranian pistachios swirled with saffron-infused royal rose milk.", 219.0, "images/pistachio-rose-milk.jpg", "Chilled Milk, Roasted Pistachios, Damask Rose Petals, Saffron", "Speciality Blends", "ARTISANAL RESERVE", 1, 0, 1, 1, 4.9, 186),
                ("Rose Badam Almond Cream", "Finely slivered Mamra badam almonds steeped in slow-chilled floral velvet milk with silver leaf.", 209.0, "images/almond-rose-milk.jpg", "Mamra Almonds, A2 Whole Milk, Rose Essence, Saffron Strands, Silver Vark", "Speciality Blends", "CHEF'S RESERVE", 1, 0, 1, 1, 4.9, 164),
                ("Tender Coconut Rose", "Tender coastal coconut cream paired with aromatic rose floral absolute for tropical luxury.", 179.0, "images/Rose Coconut Milk.jpg", "Fresh Coconut Milk, Rose Nectar, Saffron, Organic Sugar", "Speciality Blends", "EXOTIC BLEND", 1, 0, 1, 1, 4.8, 98),
                ("Dark Cocoa Rose Noir", "Rich Dutch dark cocoa balanced with the delicate floral finish of fresh damask roses.", 189.0, "images/Rose Chocolate.jpg", "Dutch Dark Cocoa, Rose Absolute, Full Cream Milk, Vanilla", "Speciality Blends", "INDULGENT", 1, 0, 1, 1, 4.9, 125),
                ("Alphonso Mango Rose", "Sun-soaked Ratnagiri Alphonso mango nectar harmonized with chilled rose whole milk.", 189.0, "images/Mango Rose Milk.jpg", "Alphonso Mango Puree, Damask Rose Milk, Honey, Cardamom", "Speciality Blends", "SUMMER SPECIAL", 1, 0, 1, 1, 4.9, 172)
            ]
            cursor.executemany("""
                INSERT INTO products (name, description, price, image, ingredients, category, badge, available, sold_out, visible, featured, rating, reviews_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, seed_products)

        # SEED 2: Admin User from Environment or Default
        env_admin_user = os.getenv("ADMIN_USERNAME", "admin").strip()
        env_admin_pass = os.getenv("ADMIN_PASSWORD", "royaladmin2026").strip()
        admin_email = os.getenv("ADMIN_EMAIL", "vikneshvaren2@gmail.com").strip()

        cursor.execute("SELECT id, password_hash FROM admin_users WHERE username = ?;", (env_admin_user,))
        existing_admin = cursor.fetchone()
        if not existing_admin:
            pw_hash = generate_password_hash(env_admin_pass)
            cursor.execute("""
                INSERT INTO admin_users (username, password_hash, email)
                VALUES (?, ?, ?);
            """, (env_admin_user, pw_hash, admin_email))
        else:
            # Sync with .env password if admin user exists
            if env_admin_pass and not check_password_hash(existing_admin["password_hash"], env_admin_pass):
                cursor.execute("""
                    UPDATE admin_users SET password_hash = ?, email = ? WHERE username = ?;
                """, (generate_password_hash(env_admin_pass), admin_email, env_admin_user))

        # SEED 3: Shop Settings
        cursor.execute("SELECT COUNT(*) AS cnt FROM shop_settings;")
        if cursor.fetchone()["cnt"] == 0:
            settings = [
                ("shop_name", "ROYAL ROSE MILK", "Brand Display Name"),
                ("phone", "+91 9445437069", "Customer Support Phone"),
                ("email", "vikneshvaren2@gmail.com", "Official Contact Email"),
                ("whatsapp", "919445437069", "WhatsApp Business Number"),
                ("address", "Tamil Nadu, India", "Heritage Location"),
                ("opening_hours", "Monday – Sunday: 9:00 AM – 10:00 PM IST", "Operating Hours"),
                ("delivery_standard_fee", "0", "Standard Delivery Fee in INR"),
                ("delivery_express_fee", "30", "Express Delivery Fee in INR")
            ]
            cursor.executemany("""
                INSERT INTO shop_settings (key, value, description)
                VALUES (?, ?, ?);
            """, settings)

        conn.commit()



# =====================================================
# PRODUCT MANAGEMENT FUNCTIONS
# =====================================================

def get_visible_products():
    """Retrieve all products visible to customers."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, description, price, image, ingredients, category, badge,
                   available, sold_out, visible, featured, rating, reviews_count
            FROM products
            WHERE visible = 1
            ORDER BY id ASC;
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_all_products_admin():
    """Retrieve all products including hidden ones for admin."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, name, description, price, image, ingredients, category, badge,
                   available, sold_out, visible, featured, rating, reviews_count, created_at, updated_at
            FROM products
            ORDER BY id ASC;
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_product_by_id(product_id):
    """Retrieve a single product by its ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE id = ?;", (product_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def add_product(name, description, price, image, ingredients="", category="Rose Milk", badge="", available=1, sold_out=0, visible=1, featured=0):
    """Add a new product to the catalogue."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, description, price, image, ingredients, category, badge, available, sold_out, visible, featured)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, (name, description, float(price), image, ingredients, category, badge, int(available), int(sold_out), int(visible), int(featured)))
        conn.commit()
        return cursor.lastrowid


def update_product(product_id, name, description, price, image=None, ingredients="", category="Rose Milk", badge="", available=1, sold_out=0, visible=1, featured=0):
    """Update an existing product."""
    with get_db() as conn:
        cursor = conn.cursor()
        if image:
            cursor.execute("""
                UPDATE products
                SET name = ?, description = ?, price = ?, image = ?, ingredients = ?,
                    category = ?, badge = ?, available = ?, sold_out = ?, visible = ?, featured = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """, (name, description, float(price), image, ingredients, category, badge, int(available), int(sold_out), int(visible), int(featured), product_id))
        else:
            cursor.execute("""
                UPDATE products
                SET name = ?, description = ?, price = ?, ingredients = ?,
                    category = ?, badge = ?, available = ?, sold_out = ?, visible = ?, featured = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?;
            """, (name, description, float(price), ingredients, category, badge, int(available), int(sold_out), int(visible), int(featured), product_id))
        conn.commit()
        return cursor.rowcount > 0


def toggle_product_sold_out(product_id):
    """Toggle a product's sold out status (0 <-> 1)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT sold_out FROM products WHERE id = ?;", (product_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Product not found."
        new_status = 0 if row["sold_out"] == 1 else 1
        cursor.execute("UPDATE products SET sold_out = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (new_status, product_id))
        conn.commit()
        return True, new_status


def toggle_product_visibility(product_id):
    """Toggle a product's visibility status (0 <-> 1)."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT visible FROM products WHERE id = ?;", (product_id,))
        row = cursor.fetchone()
        if not row:
            return False, "Product not found."
        new_status = 0 if row["visible"] == 1 else 1
        cursor.execute("UPDATE products SET visible = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?;", (new_status, product_id))
        conn.commit()
        return True, new_status


def delete_product(product_id):
    """Delete a product from the database."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id = ?;", (product_id,))
        conn.commit()
        return cursor.rowcount > 0


# =====================================================
# ADMIN AUTHENTICATION
# =====================================================

def verify_admin_credentials(username, password):
    """Verify admin login and return an auth token on success."""
    clean_user = username.strip()
    clean_pass = password.strip()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM admin_users WHERE username = ?;", (clean_user,))
        user = cursor.fetchone()
        if user and check_password_hash(user["password_hash"], clean_pass):
            token = secrets.token_hex(24)
            ADMIN_SESSIONS[token] = {
                "username": user["username"],
                "created_at": get_ist_now()
            }
            return True, token
            
        # Fallback to check against environment variables directly if DB was not synced
        env_user = os.getenv("ADMIN_USERNAME", "admin").strip()
        env_pass = os.getenv("ADMIN_PASSWORD", "royaladmin2026").strip()
        if clean_user == env_user and clean_pass == env_pass:
            token = secrets.token_hex(24)
            ADMIN_SESSIONS[token] = {
                "username": clean_user,
                "created_at": get_ist_now()
            }
            return True, token

        return False, "Invalid admin username or password."


def verify_admin_token(token):
    """Check if token is valid."""
    if not token or token not in ADMIN_SESSIONS:
        return False
    return True


def invalidate_admin_token(token):
    """Log out admin."""
    if token in ADMIN_SESSIONS:
        del ADMIN_SESSIONS[token]
        return True
    return False


def change_admin_password(username, old_password, new_password):
    """Update admin password after validating current password."""
    if not new_password or len(new_password.strip()) < 6:
        return False, "New password must be at least 6 characters."

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, username, password_hash FROM admin_users WHERE username = ?;", (username.strip(),))
        user = cursor.fetchone()
        
        if not user:
            return False, "Admin user not found."
            
        if not check_password_hash(user["password_hash"], old_password.strip()):
            return False, "Current password does not match."
            
        new_hash = generate_password_hash(new_password.strip())
        cursor.execute("UPDATE admin_users SET password_hash = ? WHERE username = ?;", (new_hash, username.strip()))
        conn.commit()
        return True, "Admin password updated successfully."


# =====================================================
# ORDER ID GENERATOR & BOOKING
# =====================================================

def generate_order_id():
    """Generates a sequential, professional unique order ID: RR-YYYYMMDD-NNN"""
    today_str = get_ist_now().strftime("%Y%m%d")
    prefix = f"RR-{today_str}-"

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT order_id FROM orders
            WHERE order_id LIKE ?
            ORDER BY id DESC
            LIMIT 1;
        """, (f"{prefix}%",))

        last_order = cursor.fetchone()

        if last_order:
            last_id_str = last_order["order_id"]
            try:
                seq_num = int(last_id_str.split("-")[-1]) + 1
            except (ValueError, IndexError):
                seq_num = 1
        else:
            seq_num = 1

        return f"{prefix}{seq_num:03d}"


def save_booking(customer_data, products_data, delivery_preference="Standard Delivery", payment_method="Cash on Delivery", notes=""):
    """
    Saves a customer booking transactionally:
    1. Checks product availability and prevents booking sold-out items.
    2. Calculates accurate server-side totals based on active DB prices.
    3. Inserts customer record.
    4. Generates unique sequential Order ID.
    5. Inserts order and order items.
    """
    with get_db() as conn:
        cursor = conn.cursor()

        # Check product availability and calculate server-side totals
        subtotal = 0.0
        validated_items = []

        for item in products_data:
            p_name = item.get("name", "").strip()
            p_qty = max(1, int(item.get("quantity", 1)))

            cursor.execute("SELECT id, name, price, available, sold_out, visible FROM products WHERE name = ? COLLATE NOCASE ORDER BY id DESC LIMIT 1;", (p_name,))
            db_product = cursor.fetchone()

            if db_product:
                if db_product["sold_out"] == 1 or db_product["available"] == 0:
                    raise ValueError(f"'{db_product['name']}' is currently SOLD OUT and cannot be booked.")
                unit_price = float(db_product["price"])
                p_id = db_product["id"]
                p_real_name = db_product["name"]
            else:
                unit_price = float(item.get("price", 149.0))
                p_id = None
                p_real_name = p_name

            item_subtotal = round(unit_price * p_qty, 2)
            subtotal += item_subtotal

            validated_items.append({
                "product_id": p_id,
                "product_name": p_real_name,
                "quantity": p_qty,
                "unit_price": unit_price,
                "subtotal": item_subtotal
            })

        # Calculate Delivery charge from settings
        cursor.execute("SELECT value FROM shop_settings WHERE key = 'delivery_express_fee';")
        exp_row = cursor.fetchone()
        exp_fee = float(exp_row["value"]) if exp_row else 30.0

        delivery_charge = exp_fee if "express" in delivery_preference.lower() else 0.0
        total_amount = round(subtotal + delivery_charge, 2)

        # Payment status defaults
        pay_clean = payment_method.strip() if payment_method else "Cash on Delivery"
        if "online" in pay_clean.lower() or "upi" in pay_clean.lower() or "card" in pay_clean.lower():
            payment_status = "PAID"
        else:
            payment_status = "CASH_ON_DELIVERY"

        # 1. Insert Customer with IST timestamp
        booking_date = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute("""
            INSERT INTO customers (name, email, phone, address, city, state, pincode, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
        """, (
            customer_data["name"].strip(),
            customer_data["email"].strip().lower(),
            customer_data["phone"].strip(),
            customer_data["address"].strip(),
            customer_data["city"].strip(),
            customer_data.get("state", "Tamil Nadu").strip(),
            customer_data["pincode"].strip(),
            booking_date
        ))
        customer_id = cursor.lastrowid

        # 2. Generate unique Order ID
        order_id = generate_order_id()

        # 3. Insert Order with explicit IST booking_date and created_at
        cursor.execute("""
            INSERT INTO orders (
                order_id, customer_id, subtotal, delivery_charge,
                total_amount, delivery_preference, payment_method, payment_status,
                order_status, notes, booking_date, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'CONFIRMED', ?, ?, ?);
        """, (
            order_id,
            customer_id,
            subtotal,
            delivery_charge,
            total_amount,
            delivery_preference,
            pay_clean,
            payment_status,
            notes,
            booking_date,
            booking_date
        ))

        # 4. Insert Order Items
        for vi in validated_items:
            cursor.execute("""
                INSERT INTO order_items (order_id, product_id, product_name, quantity, unit_price, subtotal)
                VALUES (?, ?, ?, ?, ?, ?);
            """, (
                order_id,
                vi["product_id"],
                vi["product_name"],
                vi["quantity"],
                vi["unit_price"],
                vi["subtotal"]
            ))

        conn.commit()

        return {
            "order_id": order_id,
            "customer_id": customer_id,
            "subtotal": subtotal,
            "delivery_charge": delivery_charge,
            "total_amount": total_amount,
            "total_price": total_amount,
            "total": total_amount,
            "delivery_preference": delivery_preference,
            "payment_method": pay_clean,
            "payment_status": payment_status,
            "order_status": "CONFIRMED",
            "status": "CONFIRMED",
            "notes": notes,
            "booking_date": booking_date,
            "customer": {
                "name": customer_data["name"].strip(),
                "email": customer_data["email"].strip().lower(),
                "phone": customer_data["phone"].strip(),
                "address": customer_data["address"].strip(),
                "city": customer_data["city"].strip(),
                "state": customer_data.get("state", "Tamil Nadu").strip(),
                "pincode": customer_data["pincode"].strip()
            },
            "items": validated_items
        }


# =====================================================
# ORDER TRACKING & CANCELLATION
# =====================================================

def get_order_by_id(order_id):
    """Retrieve full order details by order_id (for admin use)."""
    clean_order_id = order_id.strip().upper()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, c.name AS cust_name, c.email AS cust_email,
                   c.phone AS cust_phone, c.address AS cust_address,
                   c.city AS cust_city, c.state AS cust_state, c.pincode AS cust_pincode
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE UPPER(o.order_id) = ?;
        """, (clean_order_id,))

        row = cursor.fetchone()
        if not row:
            return None

        order_dict = dict(row)
        cursor.execute("""
            SELECT product_id, product_name, quantity, unit_price, subtotal
            FROM order_items
            WHERE order_id = ?;
        """, (order_dict["order_id"],))

        items = [dict(item_row) for item_row in cursor.fetchall()]

        return {
            "order_id": order_dict["order_id"],
            "subtotal": order_dict["subtotal"],
            "delivery_charge": order_dict["delivery_charge"],
            "total_amount": order_dict["total_amount"],
            "total_price": order_dict["total_amount"],
            "total": order_dict["total_amount"],
            "delivery_preference": order_dict.get("delivery_preference", "Standard Delivery"),
            "payment_method": order_dict.get("payment_method", "Cash on Delivery"),
            "payment_status": order_dict.get("payment_status", "PENDING"),
            "order_status": order_dict["order_status"],
            "status": order_dict["order_status"],
            "notes": order_dict.get("notes", ""),
            "booking_date": order_dict.get("booking_date", ""),
            "created_at": order_dict.get("created_at", ""),
            "cancelled_at": order_dict.get("cancelled_at"),
            "cancellation_reason": order_dict.get("cancellation_reason"),
            "cancelled_by": order_dict.get("cancelled_by"),
            "customer": {
                "name": order_dict["cust_name"],
                "email": order_dict["cust_email"],
                "phone": order_dict["cust_phone"],
                "address": order_dict["cust_address"],
                "city": order_dict["cust_city"],
                "state": order_dict.get("cust_state", "Tamil Nadu"),
                "pincode": order_dict["cust_pincode"]
            },
            "items": items
        }


def get_order_by_id_and_verification(order_id, verification):
    """
    Secure lookup: matches order_id AND (customer email or phone).
    Supports email lookup, formatted phone numbers, and digits-only phone matching.
    """
    if not order_id or not verification:
        return None

    clean_order_id = str(order_id).strip().upper()
    raw_verify = str(verification).strip()
    clean_verify = raw_verify.lower().replace(" ", "").replace("-", "")

    order = get_order_by_id(clean_order_id)
    if not order:
        return None

    stored_email = (order["customer"]["email"] or "").strip().lower()
    stored_phone = (order["customer"]["phone"] or "").strip()
    clean_stored_phone = stored_phone.lower().replace(" ", "").replace("-", "")

    # 1. Email check
    if clean_verify == stored_email:
        return order

    # 2. Direct clean phone check
    if clean_verify == clean_stored_phone:
        return order

    # 3. Digits-only normalized phone comparison (handles +91, country codes, 10-digit formats)
    verify_digits = re.sub(r"\D", "", raw_verify)
    stored_digits = re.sub(r"\D", "", stored_phone)

    if verify_digits and stored_digits:
        if verify_digits == stored_digits:
            return order
        # Match trailing 10 digits
        if len(verify_digits) >= 10 and len(stored_digits) >= 10:
            if verify_digits[-10:] == stored_digits[-10:]:
                return order
        elif verify_digits.endswith(stored_digits) or stored_digits.endswith(verify_digits):
            return order

    return None


def cancel_order(order_id, verification=None, reason="Customer requested cancellation", cancelled_by="CUSTOMER"):
    """
    Cancels an order:
    - Verifies identity if verification is provided
    - Updates order_status to 'CANCELLED'
    - Sets cancelled_at timestamp, cancellation_reason, and cancelled_by
    """
    if verification:
        order = get_order_by_id_and_verification(order_id, verification)
    else:
        order = get_order_by_id(order_id)

    if not order:
        return None, "Invalid Order ID or verification details."

    if order["order_status"] == "CANCELLED":
        return None, "This order has already been cancelled."

    if order["order_status"] == "COMPLETED":
        return None, "Completed orders cannot be cancelled."

    cancel_time = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")

    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE orders
            SET order_status = 'CANCELLED',
                cancelled_at = ?,
                cancellation_reason = ?,
                cancelled_by = ?
            WHERE order_id = ?;
        """, (cancel_time, reason, cancelled_by, order["order_id"]))
        conn.commit()

    order["order_status"] = "CANCELLED"
    order["cancelled_at"] = cancel_time
    order["cancellation_reason"] = reason
    order["cancelled_by"] = cancelled_by
    return order, "Order cancelled successfully."


def update_order_status(order_id, new_status, cancelled_by=None, reason=None):
    """Admin tool to progress order status: PENDING -> CONFIRMED -> PROCESSING -> READY / OUT FOR DELIVERY -> COMPLETED / CANCELLED."""
    valid_statuses = ["PENDING", "CONFIRMED", "PROCESSING", "READY", "OUT FOR DELIVERY", "COMPLETED", "CANCELLED"]
    status_upper = new_status.strip().upper()
    if status_upper not in valid_statuses:
        return False, f"Invalid status: {new_status}"

    clean_order_id = order_id.strip().upper()

    with get_db() as conn:
        cursor = conn.cursor()
        if status_upper == "CANCELLED":
            cancel_time = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
            cancel_by_val = cancelled_by or "ADMIN"
            reason_val = reason or "Cancelled by store administrator"
            cursor.execute("""
                UPDATE orders
                SET order_status = 'CANCELLED',
                    cancelled_at = ?,
                    cancelled_by = ?,
                    cancellation_reason = ?
                WHERE UPPER(order_id) = ?;
            """, (cancel_time, cancel_by_val, reason_val, clean_order_id))
        else:
            cursor.execute("""
                UPDATE orders
                SET order_status = ?
                WHERE UPPER(order_id) = ?;
            """, (status_upper, clean_order_id))
        conn.commit()
        return (cursor.rowcount > 0), "Order status updated successfully."


def update_order_payment_status(order_id, payment_status):
    """Update payment status for an order (PENDING, PAID, FAILED, REFUNDED, CASH_ON_DELIVERY)."""
    valid_pay_statuses = ["PENDING", "PAID", "FAILED", "REFUNDED", "CASH_ON_DELIVERY"]
    pay_upper = payment_status.strip().upper()
    if pay_upper not in valid_pay_statuses:
        return False, f"Invalid payment status: {payment_status}"

    clean_order_id = order_id.strip().upper()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE orders SET payment_status = ? WHERE UPPER(order_id) = ?;", (pay_upper, clean_order_id))
        conn.commit()
        return (cursor.rowcount > 0), f"Payment status updated to {pay_upper}."


def delete_order(order_id):
    """Safely delete an order and its order items from the database."""
    clean_order_id = order_id.strip().upper()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM order_items WHERE UPPER(order_id) = ?;", (clean_order_id,))
        cursor.execute("DELETE FROM orders WHERE UPPER(order_id) = ?;", (clean_order_id,))
        conn.commit()
        return cursor.rowcount > 0


# =====================================================
# CUSTOMER MANAGEMENT
# =====================================================

def get_all_customers_admin():
    """Retrieve all customers with order metrics for admin view."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT c.*,
                   COUNT(o.id) AS total_orders,
                   COALESCE(SUM(CASE WHEN o.order_status != 'CANCELLED' THEN o.total_amount ELSE 0 END), 0) AS total_spent,
                   MAX(o.booking_date) AS latest_order_date,
                   (SELECT order_id FROM orders WHERE customer_id = c.id ORDER BY id DESC LIMIT 1) AS latest_order_id,
                   (SELECT order_status FROM orders WHERE customer_id = c.id ORDER BY id DESC LIMIT 1) AS latest_order_status
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id
            ORDER BY c.id DESC;
        """)
        return [dict(row) for row in cursor.fetchall()]


def get_customer_orders_by_id(customer_id):
    """Retrieve all orders placed by a specific customer."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT o.*, c.name AS cust_name, c.email AS cust_email, c.phone AS cust_phone,
                   c.address AS cust_address, c.city AS cust_city, c.pincode AS cust_pincode
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            WHERE o.customer_id = ?
            ORDER BY o.id DESC;
        """, (customer_id,))
        orders_raw = [dict(row) for row in cursor.fetchall()]
        for o in orders_raw:
            cursor.execute("""
                SELECT product_id, product_name, quantity, unit_price, subtotal
                FROM order_items
                WHERE order_id = ?;
            """, (o["order_id"],))
            o["items"] = [dict(i) for i in cursor.fetchall()]
        return orders_raw


# =====================================================
# CONTACT & SETTINGS
# =====================================================

def save_contact_message(name, email, phone, message):
    """Save customer contact inquiry to database with IST timestamp."""
    created_at = get_ist_now().strftime("%Y-%m-%d %H:%M:%S")
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO contact_messages (name, email, phone, message, created_at)
            VALUES (?, ?, ?, ?, ?);
        """, (name.strip(), email.strip().lower(), phone.strip() if phone else "", message.strip(), created_at))
        conn.commit()
        return cursor.lastrowid


def get_all_contact_messages():
    """Retrieve contact messages for admin."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM contact_messages ORDER BY id DESC;")
        return [dict(row) for row in cursor.fetchall()]


def get_shop_settings():
    """Retrieve all shop settings as a key-value dictionary."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT key, value, description FROM shop_settings;")
        rows = cursor.fetchall()
        settings = {}
        for r in rows:
            settings[r["key"]] = r["value"]
        return settings


def update_shop_settings(settings_dict):
    """Update shop settings in database."""
    with get_db() as conn:
        cursor = conn.cursor()
        for k, v in settings_dict.items():
            cursor.execute("""
                INSERT INTO shop_settings (key, value, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(key) DO UPDATE SET value = excluded.value, updated_at = CURRENT_TIMESTAMP;
            """, (k, str(v)))
        conn.commit()
        return True


# =====================================================
# ADMIN DASHBOARD AGGREGATION
# =====================================================

def get_admin_dashboard_data():
    """Retrieve aggregated data for the admin dashboard."""
    with get_db() as conn:
        cursor = conn.cursor()

        # 1. Orders
        cursor.execute("""
            SELECT o.*, c.name AS cust_name, c.email AS cust_email,
                   c.phone AS cust_phone, c.address AS cust_address,
                   c.city AS cust_city, c.state AS cust_state, c.pincode AS cust_pincode
            FROM orders o
            JOIN customers c ON o.customer_id = c.id
            ORDER BY o.id DESC;
        """)
        orders_raw = [dict(row) for row in cursor.fetchall()]

        # Attach items to each order
        for o in orders_raw:
            cursor.execute("""
                SELECT product_id, product_name, quantity, unit_price, subtotal
                FROM order_items
                WHERE order_id = ?;
            """, (o["order_id"],))
            items_list = [dict(i) for i in cursor.fetchall()]
            o["items"] = items_list
            o["order_items"] = items_list

        # 2. Products
        cursor.execute("SELECT * FROM products ORDER BY id ASC;")
        products = [dict(row) for row in cursor.fetchall()]

        # 3. Customers
        cursor.execute("""
            SELECT c.*,
                   COUNT(o.id) AS total_orders,
                   COALESCE(SUM(CASE WHEN o.order_status != 'CANCELLED' THEN o.total_amount ELSE 0 END), 0) AS total_spent,
                   MAX(o.booking_date) AS latest_order_date,
                   (SELECT order_id FROM orders WHERE customer_id = c.id ORDER BY id DESC LIMIT 1) AS latest_order_id,
                   (SELECT order_status FROM orders WHERE customer_id = c.id ORDER BY id DESC LIMIT 1) AS latest_order_status
            FROM customers c
            LEFT JOIN orders o ON c.id = o.customer_id
            GROUP BY c.id
            ORDER BY c.id DESC;
        """)
        customers_raw = [dict(row) for row in cursor.fetchall()]

        # 4. Messages
        cursor.execute("SELECT * FROM contact_messages ORDER BY id DESC;")
        messages = [dict(row) for row in cursor.fetchall()]

        # 5. Settings
        settings = get_shop_settings()

        # 6. Stats computation
        total_orders = len(orders_raw)
        total_revenue = sum(o["total_amount"] for o in orders_raw if o["order_status"] != "CANCELLED")
        pending_orders = sum(1 for o in orders_raw if o["order_status"] == "PENDING")
        confirmed_orders = sum(1 for o in orders_raw if o["order_status"] == "CONFIRMED")
        processing_orders = sum(1 for o in orders_raw if o["order_status"] == "PROCESSING")
        out_for_delivery_orders = sum(1 for o in orders_raw if o["order_status"] in ["READY", "OUT FOR DELIVERY"])
        completed_orders = sum(1 for o in orders_raw if o["order_status"] == "COMPLETED")
        cancelled_orders = sum(1 for o in orders_raw if o["order_status"] == "CANCELLED")

        total_products = len(products)
        available_products = sum(1 for p in products if p["sold_out"] == 0 and p["available"] == 1)
        sold_out_products = sum(1 for p in products if p["sold_out"] == 1)
        hidden_products = sum(1 for p in products if p["visible"] == 0)
        total_customers = len(customers_raw)

        stats = {
            "total_orders": total_orders,
            "total_revenue": round(total_revenue, 2),
            "pending_orders": pending_orders,
            "confirmed_orders": confirmed_orders,
            "processing_orders": processing_orders,
            "out_for_delivery_orders": out_for_delivery_orders,
            "completed_orders": completed_orders,
            "cancelled_orders": cancelled_orders,
            "total_customers": total_customers,
            "total_products": total_products,
            "available_products": available_products,
            "sold_out_products": sold_out_products,
            "hidden_products": hidden_products,
            "unread_messages": sum(1 for m in messages if m["status"] == "UNREAD")
        }

        return {
            "stats": stats,
            "orders": orders_raw,
            "products": products,
            "customers": customers_raw,
            "messages": messages,
            "settings": settings
        }


def save_subscriber(email):
    """Saves a newsletter subscriber email safely and idempotently."""
    email_clean = str(email or "").strip().lower()
    if not email_clean:
        return False
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO newsletter_subscribers (email) VALUES (?);", (email_clean,))
        return True


def get_all_subscribers():
    """Retrieves all newsletter subscribers."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, email, created_at FROM newsletter_subscribers ORDER BY id DESC;")
        return [dict(row) for row in cursor.fetchall()]


def reset_all_orders_data():
    """Wipes all order records, items, customer records, and contact messages to start completely fresh."""
    with get_db() as conn:
        cursor = conn.cursor()
        for table in ["order_items", "orders", "customers", "contact_messages", "newsletter_subscribers"]:
            try:
                cursor.execute(f"DELETE FROM {table};")
            except Exception:
                pass
        try:
            cursor.execute("DELETE FROM sqlite_sequence WHERE name IN ('orders', 'customers', 'order_items', 'contact_messages', 'newsletter_subscribers');")
        except Exception:
            pass
        conn.commit()
        return True

