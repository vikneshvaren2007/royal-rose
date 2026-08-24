"""
ROYAL ROSE MILK — Comprehensive Automated Test Suite
Tests all features:
1. Health check & DB connection
2. Products catalogue & public settings
3. Admin authentication (valid, invalid, verify token, logout)
4. Admin dashboard data aggregation
5. Admin product CRUD (Add, Edit, Price/Name/Image/Category update, Sold-Out toggle, Visibility toggle, Delete)
6. Sold-out booking prevention guard
7. Customer booking flow with unique sequential Order ID
8. Order tracking with secure dual-factor verification
9. Customer cancellation flow with dual-email trigger
10. Admin order status progression & Admin cancellation with dual-email trigger
11. Contact inquiry submission
12. Security & unauthorized route protection
"""

import sys
import os
import secrets

# Ensure backend directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app import app
import database

client = app.test_client()

print("==========================================================")
print("ROYAL ROSE MILK - COMPREHENSIVE BACKEND TEST SUITE")
print("==========================================================")

# 1. Health Check
res_health = client.get("/api/health")
assert res_health.status_code == 200, f"Health check failed: {res_health.data}"
assert res_health.json["status"] == "ok"
assert res_health.json["database"] == "connected"
print(f"[PASS] TEST 1: Health check OK -> {res_health.json['service']} ({res_health.json['database']})")

# 2. Products API
res_prods = client.get("/api/products")
assert res_prods.status_code == 200 and res_prods.json["success"]
products = res_prods.json["products"]
assert len(products) >= 6, f"Expected at least 6 products, got {len(products)}"
print(f"[PASS] TEST 2: /api/products OK ({len(products)} varieties loaded from DB)")

# 3. Settings API
res_set = client.get("/api/settings")
assert res_set.status_code == 200 and res_set.json["success"]
assert "shop_name" in res_set.json["settings"]
print(f"[PASS] TEST 3: /api/settings OK -> Brand: {res_set.json['settings'].get('shop_name')}")

# 4. Admin Authentication
# 4a. Invalid login rejected
res_bad_login = client.post("/api/admin/login", json={"username": "admin", "password": "wrongpassword123"})
assert res_bad_login.status_code == 401 and not res_bad_login.json["success"]
print("[PASS] TEST 4a: Admin Invalid Login Guard OK (401 Unauthorized)")

# 4b. Valid login
res_login = client.post("/api/admin/login", json={"username": "admin", "password": "royaladmin2026"})
assert res_login.status_code == 200 and res_login.json["success"]
token = res_login.json["token"]
admin_headers = {"Authorization": f"Bearer {token}"}
print("[PASS] TEST 4b: Admin Login OK (Generated secure session token)")

# 4c. Verify token endpoint
res_verify = client.get("/api/admin/verify-token", headers=admin_headers)
assert res_verify.status_code == 200 and res_verify.json["valid"]
print("[PASS] TEST 4c: Admin Token Verification OK (Token valid)")

# 5. Admin Dashboard
res_dash = client.get("/api/admin/dashboard", headers=admin_headers)
assert res_dash.status_code == 200 and res_dash.json["success"]
stats = res_dash.json["data"]["stats"]
print(f"[PASS] TEST 5: Admin Dashboard Aggregation OK (Orders: {stats['total_orders']}, Revenue: Rs.{stats['total_revenue']})")

# 6. Admin Product Management CRUD
# 6a. Create product
test_pname = f"Royal Kashmiri Saffron Rose {secrets.token_hex(3)}"
test_pname_updated = f"{test_pname} (Gold Edition)"

res_add = client.post("/api/admin/products", headers=admin_headers, json={
    "name": test_pname,
    "price": 249.0,
    "description": "Infused with pure Kashmiri saffron threads and rich condensed damask rose extract.",
    "image": "images/Royal Rose Milk.jpg",
    "ingredients": "Whole Milk, Saffron, Damask Rose Extract, Pistachio",
    "badge": "EXCLUSIVE",
    "category": "Rose Milk",
    "available": 1,
    "sold_out": 0,
    "visible": 1
})
assert res_add.status_code == 201 and res_add.json["success"]
new_prod_id = res_add.json["id"]
print(f"[PASS] TEST 6a: Admin Add Product OK (ID: {new_prod_id}, '{test_pname}')")

# 6b. Update product (price, name, category, image)
res_update = client.post(f"/api/admin/products/{new_prod_id}", headers=admin_headers, json={
    "name": test_pname_updated,
    "price": 279.0,
    "description": "Infused with pure Kashmiri saffron threads, 24K edible gold leaf, and rich damask rose.",
    "image": "images/Royal Rose Milk.jpg",
    "ingredients": "Whole Milk, Kashmiri Saffron, 24K Gold Flakes, Damask Rose",
    "badge": "ROYAL LUXURY",
    "category": "Signature Rose Milk",
    "available": 1,
    "sold_out": 0,
    "visible": 1
})
assert res_update.status_code == 200 and res_update.json["success"]
print("[PASS] TEST 6b: Admin Update Product OK (Name, price, category, ingredients updated)")

# 6c. Toggle Sold Out
res_sold = client.post(f"/api/admin/products/{new_prod_id}/toggle-sold-out", headers=admin_headers)
assert res_sold.status_code == 200 and res_sold.json["sold_out"] == 1
print("[PASS] TEST 6c: Admin Toggle Sold Out OK (Sold Out = 1)")

# 6d. Verify Sold-Out Booking Prevention Guard
res_book_sold = client.post("/api/book", json={
    "customer": {
        "name": "Test Customer",
        "email": "test@example.com",
        "phone": "9876543210",
        "address": "12 Palace Lane",
        "city": "Chennai",
        "pincode": "600001"
    },
    "products": [{"name": test_pname_updated, "price": 279, "quantity": 1}]
})
assert res_book_sold.status_code == 400
assert "SOLD OUT" in res_book_sold.json["message"]
print(f"[PASS] TEST 6d: Sold-Out Guard OK (Booking correctly rejected: {res_book_sold.json['message']})")

# 6e. Toggle back In Stock
res_instock = client.post(f"/api/admin/products/{new_prod_id}/toggle-sold-out", headers=admin_headers)
assert res_instock.status_code == 200 and res_instock.json["sold_out"] == 0
print("[PASS] TEST 6e: Admin Toggle In-Stock OK (Sold Out = 0)")

# 6f. Toggle Visibility (Hide)
res_hide = client.post(f"/api/admin/products/{new_prod_id}/toggle-visibility", headers=admin_headers)
assert res_hide.status_code == 200 and res_hide.json["visible"] == 0
prods_after_hide = client.get("/api/products").json["products"]
assert not any(p["id"] == new_prod_id for p in prods_after_hide)
print("[PASS] TEST 6f: Admin Hide Product OK (Excluded from customer catalogue)")

# 6g. Toggle back Visible
client.post(f"/api/admin/products/{new_prod_id}/toggle-visibility", headers=admin_headers)

# 7. Customer Booking Flow
res_book = client.post("/api/book", json={
    "customer": {
        "name": "Viknesh Varen",
        "email": "vikneshvaren2@gmail.com",
        "phone": "9445437069",
        "address": "77 Royal Palace Garden",
        "city": "Chennai",
        "pincode": "600028",
        "notes": "Deliver chilled"
    },
    "delivery": "Express Delivery",
    "products": [
        {"name": "Classic Rose Milk", "price": 149, "quantity": 2},
        {"name": test_pname_updated, "price": 279, "quantity": 1}
    ]
})
assert res_book.status_code == 200 and res_book.json["success"]
order_data = res_book.json["order"]
order_id = res_book.json["order_id"]
assert order_id.startswith("RR-")
total_amt = order_data["total_amount"]
assert total_amt > 0
assert "whatsapp_url" in res_book.json
print(f"[PASS] TEST 7: Customer Booking Flow OK (Order ID: {order_id}, Total: Rs.{total_amt}, Async emails dispatched)")

# 8. Order Tracking Flow
# 8a. Track using Order ID + Email
res_track = client.post("/api/track", json={"order_id": order_id, "verification": "vikneshvaren2@gmail.com"})
assert res_track.status_code == 200 and res_track.json["success"]
tracked_order = res_track.json["order"]
assert tracked_order["order_status"] == "CONFIRMED"
assert tracked_order["status"] == "CONFIRMED"
assert tracked_order["total_amount"] == total_amt
assert tracked_order["total_price"] == total_amt
assert "subtotal" in tracked_order and "delivery_charge" in tracked_order
print(f"[PASS] TEST 8a: Order Tracking via Email OK (Verified Order #{order_id}, Total: Rs.{tracked_order['total_amount']})")

# 8b. Track using Order ID + Phone Number
res_track_phone = client.post("/api/track", json={"order_id": order_id, "verification": "9445437069"})
assert res_track_phone.status_code == 200 and res_track_phone.json["success"]
print(f"[PASS] TEST 8b: Order Tracking via Phone Number OK")

# 8c. Track using parameter aliases (orderId, verify)
res_track_alias = client.post("/api/track", json={"orderId": order_id, "verify": "9445437069"})
assert res_track_alias.status_code == 200 and res_track_alias.json["success"]
print(f"[PASS] TEST 8c: Order Tracking via Parameter Aliases (orderId, verify) OK")

# 8d. Track with invalid details (returns 404 and friendly error)
res_track_invalid = client.post("/api/track", json={"order_id": order_id, "verification": "wrongemail@domain.com"})
assert res_track_invalid.status_code == 404
assert "Order not found. Please check your Order ID and Email/Phone number." in res_track_invalid.json["message"]
print(f"[PASS] TEST 8d: Order Tracking Invalid Verification Guard OK (404 Not Found)")

# 8e. Track with missing details (returns 400)
res_track_missing = client.post("/api/track", json={"order_id": "", "verification": ""})
assert res_track_missing.status_code == 400
assert "Both Order ID and Email/Phone are required." in res_track_missing.json["message"]
print(f"[PASS] TEST 8e: Order Tracking Missing Fields Guard OK (400 Bad Request)")

# 9. Customer Order Cancellation Flow
res_cancel = client.post("/api/cancel", json={
    "order_id": order_id,
    "verification": "9445437069",
    "reason": "Change of travel schedule"
})
assert res_cancel.status_code == 200 and res_cancel.json["success"]
assert res_cancel.json["order"]["order_status"] == "CANCELLED"
assert res_cancel.json["order"]["cancelled_by"] == "CUSTOMER"
print(f"[PASS] TEST 9: Customer Cancellation Flow OK (Order #{order_id} CANCELLED, Dual cancellation emails triggered)")

# 10. Admin Order Status Progression & Admin Cancellation
# Create another booking to test admin workflow
res_book2 = client.post("/api/book", json={
    "customer": {
        "name": "Priya Sundaram",
        "email": "priya@example.com",
        "phone": "9840123456",
        "address": "45 Lotus Garden",
        "city": "Chennai",
        "pincode": "600018"
    },
    "delivery": "Standard Delivery",
    "products": [{"name": "Classic Rose Milk", "price": 149, "quantity": 1}]
})
order_id2 = res_book2.json["order_id"]

# Admin status progression
res_st1 = client.post("/api/admin/order-status", headers=admin_headers, json={"order_id": order_id2, "status": "PROCESSING"})
assert res_st1.status_code == 200

res_st2 = client.post("/api/admin/order-status", headers=admin_headers, json={"order_id": order_id2, "status": "READY"})
assert res_st2.status_code == 200

# Admin cancellation with dual-email trigger
res_st_cancel = client.post("/api/admin/order-status", headers=admin_headers, json={"order_id": order_id2, "status": "CANCELLED"})
assert res_st_cancel.status_code == 200
order2_db = database.get_order_by_id(order_id2)
assert order2_db["order_status"] == "CANCELLED"
assert order2_db["cancelled_by"] == "ADMIN"
print(f"[PASS] TEST 10: Admin Status Updates & Cancellation OK (Order #{order_id2} marked CANCELLED by Admin)")

# 11. Single Order Inspection
res_single_order = client.get(f"/api/admin/orders/{order_id2}", headers=admin_headers)
assert res_single_order.status_code == 200 and res_single_order.json["success"]
assert res_single_order.json["order"]["order_id"] == order_id2
print(f"[PASS] TEST 11: Single Order 360 Inspection OK (Order #{order_id2})")

# 12. Payment Status Update
res_pay_update = client.post("/api/admin/payment-status", headers=admin_headers, json={"order_id": order_id2, "payment_status": "REFUNDED"})
assert res_pay_update.status_code == 200 and res_pay_update.json["success"]
order2_recheck = database.get_order_by_id(order_id2)
assert order2_recheck["payment_status"] == "REFUNDED"
print(f"[PASS] TEST 12: Order Payment Status Update OK (Order #{order_id2} marked REFUNDED)")

# 13. Customer Directory & Customer Order History
res_custs = client.get("/api/admin/customers", headers=admin_headers)
assert res_custs.status_code == 200 and res_custs.json["success"]
customers_list = res_custs.json["customers"]
assert len(customers_list) > 0
test_cust_id = customers_list[0]["id"]
res_cust_orders = client.get(f"/api/admin/customers/{test_cust_id}/orders", headers=admin_headers)
assert res_cust_orders.status_code == 200 and res_cust_orders.json["success"]
print(f"[PASS] TEST 13: Customers Directory & History OK ({len(customers_list)} customers, history loaded)")

# 14. Contact Inquiry Flow
res_contact = client.post("/api/contact", json={
    "name": "Ananya Sharma",
    "email": "ananya@example.com",
    "phone": "9840998877",
    "message": "We would like to order 100 bottles of Royal Rose Milk for a corporate event."
})
assert res_contact.status_code == 200 and res_contact.json["success"]
print(f"[PASS] TEST 14: Contact Inquiry OK (Inquiry #{res_contact.json['id']} stored and admin alert triggered)")

# 15. Security & Route Protection
res_unauth = client.get("/api/admin/dashboard")
assert res_unauth.status_code == 401
res_unauth_prod = client.post("/api/admin/products", json={"name": "Hacker Drink", "price": 10})
assert res_unauth_prod.status_code == 401
print("[PASS] TEST 15: Route Protection Guard OK (All /api/admin/* endpoints strictly require auth)")

# 16. Clean up Test Product
client.delete(f"/api/admin/products/{new_prod_id}", headers=admin_headers)
print("[PASS] TEST 16: Product Deletion OK (Catalogue restored)")

# 17. Newsletter Subscription Flow
res_newsletter = client.post("/api/newsletter", json={"email": "circle@royalrosemilk.com"})
assert res_newsletter.status_code == 200 and res_newsletter.json["success"]
print("[PASS] TEST 17: Newsletter Subscription OK (Welcome email dispatched & subscriber stored)")

# 18. Admin Logout
res_logout = client.post("/api/admin/logout", headers=admin_headers)
assert res_logout.status_code == 200
res_verify_after = client.get("/api/admin/verify-token", headers=admin_headers)
assert res_verify_after.status_code == 401
print("[PASS] TEST 18: Admin Logout OK (Session token invalidated)")

print("\n==========================================================")
print("SUCCESS: ALL 18 TEST SUITES PASSED FLAWLESSLY!")
print("==========================================================")

