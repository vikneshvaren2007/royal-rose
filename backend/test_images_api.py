import urllib.request
import json
import os

images = [
    'images/Classic Rose Milk.jpg',
    'images/Royal Rose Milk.jpg',
    'images/strawberry-rose.jpg',
    'images/cardamom-rose-milk.jpg',
    'images/saffron-rose-milk.jpg',
    'images/pistachio-rose-milk.jpg',
    'images/almond-rose-milk.jpg',
    'images/Rose Coconut Milk.jpg',
    'images/Rose Chocolate.jpg',
    'images/Mango Rose Milk.jpg'
]

print("=== 10 UNIQUE PRODUCT IMAGES VERIFICATION ===")
for img in images:
    path = os.path.join(r"c:\Users\acer\OneDrive\Desktop\new2", img)
    exists = os.path.exists(path)
    size = os.path.getsize(path) if exists else 0
    print(f"{img:35} -> Exists: {exists}, Size: {size:,} bytes")
    assert exists and size > 0, f"Image {img} does not exist or is empty!"

print("\n=== FLASK PRODUCTS API VALIDATION ===")
req = urllib.request.urlopen("http://127.0.0.1:5000/api/products")
data = json.loads(req.read().decode("utf-8"))
assert data["success"]
products = data["products"]
print(f"Total products returned from /api/products: {len(products)}")
for p in products:
    print(f"ID {p['id']:2} | {p['category']:20} | {p['name']:30} | Rs.{p['price']} | {p['image']}")

assert len(products) == 10, f"Expected 10 products, got {len(products)}"
print("\nALL 10 UNIQUE PRODUCT IMAGES & API VERIFICATIONS PASSED 100%!")
