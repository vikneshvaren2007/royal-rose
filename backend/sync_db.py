import sys
import os

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))
import database

with database.get_db() as conn:
    cursor = conn.cursor()
    cursor.execute("DELETE FROM products;")
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
    conn.commit()

prods = database.get_visible_products()
print(f"Database synchronized successfully! Total products: {len(prods)}")
for p in prods:
    print(f"[{p['id']}] {p['category']:20} | {p['name']:30} (Rs.{p['price']}) -> {p['image']}")
