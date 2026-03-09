"""
Phase 1 (Fallback): Generate 500 realistic sample lost-and-found items
with REAL images downloaded from picsum.photos.

Usage:
    python create_sample_data.py
"""

import os
import csv
import random
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "scraped_products.csv")
TOTAL_ITEMS = 500
IMAGE_SIZE = 300
MAX_DOWNLOAD_WORKERS = 10

# ---------------------------------------------------------------------------
# Product templates — base items to generate variations from
# ---------------------------------------------------------------------------

PRODUCTS = {
    "Electronics": [
        ("Sony WH-1000XM5 Wireless Headphones", "Over-ear noise cancelling wireless headphones with 30-hour battery life", 348.00),
        ("Apple AirPods Pro 2nd Gen", "Wireless earbuds with active noise cancellation and MagSafe charging case", 249.00),
        ("Samsung Galaxy Buds2 Pro", "Wireless earbuds with intelligent ANC and 360 audio", 199.99),
        ("JBL Flip 6 Portable Speaker", "Bluetooth speaker, waterproof IP67, 12 hours playtime", 129.95),
        ("Anker PowerCore 20000mAh Power Bank", "Portable charger with dual USB ports and fast charging", 45.99),
        ("Logitech M720 Wireless Mouse", "Ergonomic wireless mouse with Bluetooth and USB receiver", 49.99),
        ("SanDisk 128GB USB Flash Drive", "USB 3.0 flash drive with retractable connector", 14.99),
        ("Casio FX-991EX Scientific Calculator", "Scientific calculator with natural textbook display and 552 functions", 24.99),
        ("HP 15 Laptop Charger 65W", "65W USB-C laptop charger with blue tip connector for HP laptops", 34.99),
        ("Bose SoundLink Micro Speaker", "Small rugged Bluetooth speaker with built-in strap, waterproof", 99.00),
        ("Xiaomi Mi Band 7 Fitness Tracker", "Fitness band with AMOLED display and heart rate monitor", 49.99),
        ("Amazon Kindle Paperwhite 11th Gen", "6.8 inch e-reader with warm light and 8GB storage, waterproof", 139.99),
        ("Dell Wired USB Keyboard KB216", "Slim wired keyboard with chiclet keys and multimedia shortcuts", 16.99),
        ("Apple Lightning EarPods", "Wired earphones with Lightning connector and built-in remote", 19.00),
        ("Realme 10000mAh Power Bank 2i", "Slim power bank with dual output ports and LED indicator", 15.99),
        ("Lenovo ThinkPad USB-C Dock", "Docking station with HDMI, USB-A, USB-C, and Ethernet ports", 89.99),
        ("TP-Link Portable WiFi Router", "Compact 4G LTE mobile WiFi hotspot with 2000mAh battery", 39.99),
        ("Creative Pebble V3 Desktop Speakers", "USB-C desktop speakers with Bluetooth 5.0 and 8W output", 35.99),
        ("Portronics Konnect USB-C Hub 6-in-1", "Multi-port adapter with HDMI, USB-A, SD card slots", 29.99),
        ("Boat Rockerz 450 Wireless Headphones", "On-ear wireless headphones with 40mm drivers and 15-hour battery", 29.99),
    ],
    "Bags": [
        ("Herschel Little America Backpack", "Navy blue backpack with brown leather straps and laptop compartment", 109.99),
        ("Nike Brasilia Training Duffel Bag", "Medium duffel bag with Nike swoosh and separate shoe compartment", 45.00),
        ("JanSport SuperBreak Backpack", "Classic backpack with front utility pocket and padded shoulder straps", 36.00),
        ("Fjallraven Kanken Classic", "Rectangular backpack with top handles and reflective logo", 80.00),
        ("Adidas Alliance II Sackpack", "Drawstring bag with Adidas logo and front zip pocket", 18.00),
        ("Samsonite Laptop Messenger Bag", "Charcoal grey messenger bag with padded 15.6 inch laptop pocket", 59.99),
        ("Vera Bradley Lunch Bag", "Floral print insulated lunch bag with zip closure and ID window", 34.00),
        ("American Tourister Laptop Backpack", "Polyester backpack with padded laptop sleeve and rain cover", 42.00),
        ("Wildcraft Turnaround Polyester Backpack", "Casual backpack with padded back panel and multiple compartments", 29.99),
        ("Skybags Brat Daypack 22L", "Compact daypack with organizer pocket and key hook", 22.00),
        ("Safari Polyester Travel Sling Bag", "Crossbody sling bag with anti-theft zip pocket", 18.99),
        ("Puma Phase Backpack II", "Backpack with Puma cat logo and padded handle", 28.00),
        ("Decathlon Kipsta 20L Sports Bag", "Compact sports bag with shoe compartment and ventilation window", 15.00),
        ("Tommy Hilfiger Mini Crossbody Bag", "Faux leather small crossbody bag with TH monogram buckle", 65.00),
        ("Lululemon Everywhere Belt Bag", "Pale pink 1L belt bag with adjustable strap", 38.00),
        ("Aristocrat Polyester Travel Backpack", "Large 40L travel backpack with multiple pockets and shoe bag", 35.00),
        ("Gear Campus 8 Backpack 24L", "Blue and grey school backpack with padded straps", 18.99),
        ("VIP Highlander Laptop Backpack", "Water-resistant laptop backpack with USB charging port", 42.00),
        ("F Gear Military Tactical Backpack", "Olive green tactical backpack with MOLLE system and rain cover", 30.00),
        ("Flying Machine Canvas Backpack", "Beige canvas casual backpack with leather trim details", 45.00),
    ],
    "Clothing": [
        ("North Face Thermoball Eco Jacket", "Lightweight puffer jacket with synthetic insulation and packable design", 230.00),
        ("Levi's 501 Original Fit Jeans", "Medium wash blue jeans, straight leg, button fly", 69.50),
        ("Champion Reverse Weave Hoodie", "Oxford grey pullover hoodie with embroidered C logo on sleeve", 65.00),
        ("Adidas Ultraboost 22 Running Shoes", "Running shoes with Boost midsole", 190.00),
        ("Ray-Ban Wayfarer Classic Sunglasses", "Sunglasses with green G-15 lenses and thick frame", 163.00),
        ("Under Armour Tech 2.0 T-Shirt", "Short sleeve training t-shirt with moisture wicking fabric", 25.00),
        ("Columbia Bora Bora Booney Hat", "Wide-brim sun hat with adjustable chin strap and UPF 50", 35.00),
        ("Nike Dri-FIT Track Pants", "Slim-fit joggers with elastic waistband and zip pockets", 55.00),
        ("Uniqlo Ultra Light Down Vest", "Packable down vest with snap buttons and two front pockets", 49.90),
        ("Crocs Classic Clogs", "Rubber clogs with ventilation holes and pivoting heel strap", 49.99),
        ("Woodland Leather Belt", "Genuine leather belt with brushed metal buckle", 22.00),
        ("Puma Essential Logo Tee", "Cotton round neck t-shirt with large Puma logo on chest", 19.99),
        ("Decathlon Kalenji Running Shorts", "Lightweight running shorts with inner brief and zip pocket", 12.99),
        ("H&M Denim Jacket", "Light wash blue denim jacket with button closure and chest pockets", 39.99),
        ("New Balance 574 Sneakers", "Classic retro sneakers with suede and mesh upper", 84.99),
        ("Zara Oversized Blazer", "Structured oversized blazer with peak lapels", 79.90),
        ("Gap Classic Khaki Chinos", "Straight fit chino pants with wrinkle-free finish", 44.99),
        ("U.S. Polo Assn. Polo T-Shirt", "Cotton polo t-shirt with embroidered logo", 24.99),
        ("Allen Solly Formal Shirt", "White cotton formal shirt with spread collar", 29.99),
        ("Reebok Classic Leather Sneakers", "White leather low-top sneakers with gum sole", 75.00),
    ],
    "Books": [
        ("Calculus Early Transcendentals 8th Ed", "James Stewart calculus textbook, hard cover, blue and white", 150.00),
        ("Introduction to Algorithms (CLRS)", "Cormen et al, hardcover, maroon/dark red cover, 1292 pages", 85.00),
        ("The Great Gatsby - F. Scott Fitzgerald", "Paperback, classic blue cover with gold lettering and art deco eyes", 9.99),
        ("Organic Chemistry by Klein", "3rd edition textbook with green cover and molecular diagrams", 120.00),
        ("Psychology 101 Textbook", "Introduction to Psychology, 4th edition, purple cover with brain illustration", 95.00),
        ("Moleskine Classic Notebook Large", "Hardcover ruled notebook, 5x8.25 inches, elastic band closure", 19.95),
        ("Harry Potter and the Prisoner of Azkaban", "Paperback, illustrated cover with Buckbeak the hippogriff", 12.99),
        ("Engineering Mechanics by R.S. Khurmi", "Hardcover engineering mechanics textbook, 800 pages", 12.00),
        ("Digital Logic by Morris Mano", "Soft cover digital design textbook, 5th edition", 55.00),
        ("Let Us C by Yashavant Kanetkar", "Paperback C programming guide, 16th edition", 7.99),
        ("Sapiens by Yuval Noah Harari", "Paperback with brown/beige cover, a brief history of humankind", 14.99),
        ("Atomic Habits by James Clear", "White cover paperback with bold orange and black title text", 16.99),
        ("Oxford Advanced Learner's Dictionary", "Hardcover English dictionary, 10th edition, 1900 pages", 30.00),
        ("Data Structures Using C by Reema Thareja", "Grey and orange textbook on data structures", 9.50),
        ("Rich Dad Poor Dad by Robert Kiyosaki", "Purple paperback personal finance book with gold lettering", 11.99),
        ("The Alchemist by Paulo Coelho", "Paperback with desert illustration, philosophical novel", 10.99),
        ("Thinking Fast and Slow by Daniel Kahneman", "White paperback on psychology and decision-making", 15.99),
        ("Clean Code by Robert C. Martin", "Hardcover with blue cover, software craftsmanship guide", 39.99),
        ("The Art of War by Sun Tzu", "Small paperback, classic military strategy text", 6.99),
        ("Operating System Concepts by Silberschatz", "Yellow cover hardcover OS textbook, 10th edition", 89.99),
    ],
    "Accessories": [
        ("Hydro Flask 32oz Water Bottle", "Insulated stainless steel water bottle with straw lid", 44.95),
        ("Apple Watch SE 2nd Gen", "Space grey aluminum 44mm smartwatch with sport band", 279.00),
        ("Fossil Grant Chronograph Watch", "Brown leather strap analog watch with Roman numerals", 99.99),
        ("Oakley Holbrook Sunglasses", "Sport sunglasses with Prizm grey polarized lenses", 186.00),
        ("Tile Mate Bluetooth Tracker", "Small square Bluetooth item finder, attaches to keys", 24.99),
        ("Anker USB-C to USB-C Cable 6ft", "Braided USB-C charging cable, 6 feet, 100W PD", 13.99),
        ("Nalgene Wide Mouth 32oz Bottle", "Translucent BPA-free water bottle with loop-top cap", 14.99),
        ("Boat Bassheads 100 Wired Earphones", "In-ear wired earphones with mic, 3.5mm jack", 6.99),
        ("Fastrack UV Protected Aviator Sunglasses", "Metal frame aviator sunglasses with tinted lenses", 18.00),
        ("Milton Thermosteel Flask 500ml", "Stainless steel vacuum flask with screw lid", 12.00),
        ("Skullcandy Ink'd Wired Earbuds", "Wired earbuds with in-line mic and noise isolation", 15.99),
        ("Casio A168WA Classic Digital Watch", "Retro digital watch with stainless steel band", 29.00),
        ("Rain Umbrella Compact Folding", "Automatic open/close compact umbrella with windproof frame", 14.99),
        ("Cello Duro Tuff Steel Water Bottle 900ml", "Blue stainless steel water bottle with copper lining", 9.99),
        ("Wildcraft Polyester Wallet", "Grey trifold wallet with Velcro closure and coin pocket", 10.00),
        ("Mi Compact Bluetooth Speaker 2", "Small round Bluetooth speaker with aluminium body", 14.99),
        ("Noise ColorFit Pulse Smartwatch", "Square dial smartwatch with SpO2 and heart rate monitor", 34.99),
        ("Titan Raga Women's Watch", "Gold-toned analog watch with bracelet style strap", 65.00),
        ("Philips SHB1505 Bluetooth Earphones", "Neckband style wireless earphones with inline mic", 19.99),
        ("Cross ATX Ballpoint Pen", "Chrome ballpoint pen with twist mechanism and gift box", 35.00),
    ],
    "Sports Equipment": [
        ("Wilson NCAA Official Basketball", "Composite leather indoor/outdoor basketball, size 7", 29.99),
        ("Yonex Nanoray 10F Badminton Racket", "Lightweight badminton racket with isometric head", 34.99),
        ("Speedo Vanquisher 2.0 Swim Goggles", "Clear lens swim goggles with anti-fog coating", 20.00),
        ("Nike Flight Premium Match Soccer Ball", "Aerodynamic soccer ball, FIFA quality approved", 49.99),
        ("Manduka PRO Yoga Mat", "6mm thick professional yoga mat with dense cushioning", 120.00),
        ("TaylorMade RBZ SpeedLite Golf Club Set", "11-piece golf club set with stand bag", 599.99),
        ("Everlast Pro Style Training Gloves", "14oz boxing gloves with mesh palm", 29.99),
        ("Cosco Cricket Bat Kashmir Willow", "Full size cricket bat with cane handle and rubber grip", 22.00),
        ("Nivia Storm Football Size 5", "Machine stitched football, regulation size 5", 12.00),
        ("Li-Ning Smash XP 90 II Badminton Racket", "Isometric frame badminton racket with full cover", 18.99),
        ("Strauss Yoga Block EVA Foam", "EVA foam yoga block, 9x6x4 inches, lightweight", 8.99),
        ("Decathlon Artengo Table Tennis Bat", "3-star table tennis paddle with flared grip", 14.00),
        ("Nivia Heavy Tennis Ball Pack of 6", "Heavy-weight cricket practice tennis balls", 5.99),
        ("Vector X Wrist Support Band", "Elastic wrist support wrap with thumb loop", 4.99),
        ("Kookaburra Kahuna Cricket Gloves", "Batting gloves with reinforced finger protection", 35.00),
        ("Adidas Finale UEFA Champions League Ball", "Official replica match ball with stars design", 35.00),
        ("Head Ti.S6 Tennis Racket", "Titanium tennis racket with oversized head", 59.99),
        ("Fitbit Inspire 3 Fitness Tracker", "Slim fitness tracker with stress management and sleep tracking", 99.95),
        ("SG Cricket Helmet", "Adjustable cricket helmet with mesh visor and chin strap", 28.00),
        ("Nike Mercurial Football Boots", "Lightweight football boots with ACC technology", 120.00),
    ],
    "Stationery": [
        ("Apple iPad 10th Gen with Pencil", "10.9 inch tablet with 64GB storage and Apple Pencil", 449.00),
        ("Staedtler Triplus Fineliner Set", "20-color set of fine tip marker pens in desktop stand case", 18.49),
        ("Texas Instruments TI-84 Plus CE", "Graphing calculator with color display and rechargeable battery", 118.00),
        ("Five Star 5-Subject Notebook", "200-page college-ruled spiral notebook with 5 divider tabs", 11.49),
        ("Zebra Sarasa Clip Gel Pen Set", "10-pack retractable gel pens with rubber grip", 12.99),
        ("Post-it Super Sticky Notes 3x3", "Pack of 12 pads in bright neon colors", 18.99),
        ("Swingline Desktop Stapler", "Metal stapler with 20-sheet capacity and built-in remover", 8.49),
        ("Classmate Pulse Notebook 6-Subject", "Single line ruled 300-page spiral notebook with soft cover", 4.99),
        ("Faber-Castell Geometry Box", "Metal geometry instrument box with compass and protractor", 6.99),
        ("Parker Vector Standard Fountain Pen", "Matte fountain pen with stainless steel nib", 8.99),
        ("Cello Butterflow Ball Pen Pack of 10", "Smooth writing ball pens with comfortable grip", 2.50),
        ("Doms Colour Pencils 24 Shades", "24-shade colour pencil set in flat tin box with sharpener", 3.99),
        ("Camlin Kokuyo Geometry Box", "Plastic geometry set with compass, set squares, protractor", 3.99),
        ("Luxor WhiteBoard Markers Set of 4", "4 whiteboard markers in red, blue, green, black", 4.49),
        ("Maped 30cm Ruler Transparent", "Transparent plastic 30cm ruler with raised markings", 1.99),
        ("Pilot V7 Hi-Tecpoint Pen", "Liquid ink rollerball pen with fine 0.7mm tip", 2.99),
        ("Scotch Heavy Duty Packaging Tape", "Clear packing tape with dispenser, 48mm x 50m", 5.99),
        ("Kangaro Desk Punch DP-480", "2-hole paper punch with 12-sheet capacity", 7.99),
        ("Natraj 621 Pencils Pack of 10", "HB graphite pencils with eraser tip", 1.49),
        ("Solo Executive Portfolio Folder", "Faux leather A4 folder with notepad and card holders", 14.99),
    ],
}

# ---------------------------------------------------------------------------
# Colors, locations, and description templates
# ---------------------------------------------------------------------------
COLORS = [
    "Black", "White", "Grey", "Navy blue", "Red", "Dark green", "Brown",
    "Teal", "Silver", "Pink", "Yellow", "Olive", "Maroon", "Charcoal",
    "Royal blue", "Orange", "Beige", "Light blue", "Purple", "Mint green",
]

LOCATIONS = [
    "near the library", "in the cafeteria", "at the bus stop",
    "in the lecture hall", "near the gym", "in the computer lab",
    "in the student center", "near the parking lot", "in the auditorium",
    "at the sports complex", "in the art room", "in the laundry room",
    "near the dormitory entrance", "in the common room", "at the canteen",
    "in the chemistry lab", "near the main gate", "in the seminar hall",
    "at the basketball court", "in the reading room", "near the ATM",
    "in the washroom", "by the vending machine", "in the hostel lobby",
    "at the cricket ground", "in the dance studio", "near the admin block",
    "in the mechanical workshop", "at the food court", "in the garden area",
]

LOST_TEMPLATES = [
    "I lost my {color} {item} somewhere {loc}, I think it was {detail}",
    "Can't find my {color} {item}, I last had it {loc}, it's {detail}",
    "My {color} {item} went missing {loc}, it's the one that's {detail}",
    "Left my {color} {item} {loc} and someone might have taken it, it's {detail}",
    "I think I dropped my {color} {item} {loc}, it's {detail}",
    "Has anyone seen a {color} {item}? I lost it {loc}, it was {detail}",
    "Missing my {color} {item} since yesterday, probably {loc}, it's {detail}",
    "Somebody please help me find my {color} {item}, I left it {loc}, {detail}",
]

DETAILS = [
    "kind of scratched up from daily use",
    "pretty new, bought it last month",
    "has a small sticker on it",
    "a bit faded but still works great",
    "has my initials written somewhere on it",
    "the one with a keychain attached",
    "slightly worn out but important to me",
    "has a crack on one side",
    "the everyday-use kind",
    "a little dusty but in good condition",
    "the one I use for college",
    "got it as a birthday gift",
    "fairly common looking but mine has a tiny mark",
    "medium-sized, nothing fancy",
    "the standard one everyone uses",
]

# ---------------------------------------------------------------------------
# Image download
# ---------------------------------------------------------------------------

def download_real_image(product_id: int, product_name: str) -> str:
    """Download a real image from picsum.photos using a deterministic seed."""
    filename = f"product_{product_id:03d}.jpg"
    filepath = os.path.join(IMAGES_DIR, filename)

    if os.path.exists(filepath):
        return os.path.join("images", filename)

    # Use a hash of the product name as seed → same product always gets same image
    seed = int(hashlib.md5(f"{product_name}_{product_id}".encode()).hexdigest()[:8], 16) % 100000
    url = f"https://picsum.photos/seed/{seed}/{IMAGE_SIZE}/{IMAGE_SIZE}"

    try:
        resp = requests.get(url, timeout=20, allow_redirects=True)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            f.write(resp.content)
        return os.path.join("images", filename)
    except Exception:
        return ""


def download_images_parallel(items: list[dict]) -> dict:
    """Download images in parallel for speed. Returns {product_id: image_path}."""
    results = {}
    with ThreadPoolExecutor(max_workers=MAX_DOWNLOAD_WORKERS) as executor:
        futures = {
            executor.submit(
                download_real_image,
                item["product_id"],
                item["product_name"]
            ): item["product_id"]
            for item in items
        }
        for future in tqdm(as_completed(futures), total=len(futures), desc="Downloading images"):
            pid = futures[future]
            try:
                results[pid] = future.result()
            except Exception:
                results[pid] = ""
    return results


# ---------------------------------------------------------------------------
# Generate 500 items from templates
# ---------------------------------------------------------------------------

def generate_items(count: int = TOTAL_ITEMS) -> list[dict]:
    """Generate `count` unique product items from templates with variations."""
    random.seed(42)  # Reproducible output
    all_items = []
    product_id = 0
    categories = list(PRODUCTS.keys())

    # First pass: use all base products as-is (140 products)
    for cat in categories:
        for name, desc, price in PRODUCTS[cat]:
            product_id += 1
            color = random.choice(COLORS)
            loc = random.choice(LOCATIONS)
            detail = random.choice(DETAILS)
            template = random.choice(LOST_TEMPLATES)

            short_name = name.split("(")[0].split(" by ")[0].split(" - ")[0].strip()
            short_name_words = short_name.split()
            vague_item = " ".join(short_name_words[-2:]) if len(short_name_words) > 2 else short_name

            lost_desc = template.format(
                color=color, item=vague_item, loc=loc, detail=detail
            )

            all_items.append({
                "product_id": product_id,
                "product_name": name,
                "category": cat,
                "description": f"{color} {desc}",
                "price": f"{price:.2f}",
                "image_url": "",
                "image_path": "",
                "lost_item_description": lost_desc,
            })

    # Second pass: generate variations to reach target count
    while len(all_items) < count:
        cat = random.choice(categories)
        base_name, base_desc, base_price = random.choice(PRODUCTS[cat])
        color = random.choice(COLORS)
        loc = random.choice(LOCATIONS)
        detail = random.choice(DETAILS)
        template = random.choice(LOST_TEMPLATES)

        # Create a variation name
        variation_suffix = random.choice([
            " (New Edition)", " (Limited)", " v2", " (Used)", " (Like New)",
            " (Campus Edition)", " - Student", " (Pack of 2)", " (Renewed)",
            " (Bundle)", " (Slim)", " (Compact)", " (XL)", " (Mini)", " (Pro)",
        ])
        var_name = base_name + variation_suffix

        # Make sure name is unique
        existing_names = {i["product_name"] for i in all_items}
        if var_name in existing_names:
            continue

        product_id += 1
        # Vary the price slightly
        price_factor = random.uniform(0.7, 1.3)
        price = round(base_price * price_factor, 2)

        short_name = base_name.split("(")[0].split(" by ")[0].split(" - ")[0].strip()
        short_name_words = short_name.split()
        vague_item = " ".join(short_name_words[-2:]) if len(short_name_words) > 2 else short_name

        lost_desc = template.format(
            color=color, item=vague_item, loc=loc, detail=detail
        )

        all_items.append({
            "product_id": product_id,
            "product_name": var_name,
            "category": cat,
            "description": f"{color} {base_desc}",
            "price": f"{price:.2f}",
            "image_url": "",
            "image_path": "",
            "lost_item_description": lost_desc,
        })

    return all_items[:count]


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Phase 1: Generate Sample Lost & Found Data")
    print(f"  Target: {TOTAL_ITEMS} items with REAL images")
    print("=" * 60)

    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    # Step 1: Generate items
    print(f"\n[Step 1/3] Generating {TOTAL_ITEMS} product items...")
    items = generate_items(TOTAL_ITEMS)
    print(f"  ✅ Generated {len(items)} items\n")

    # Step 2: Download real images in parallel
    print(f"[Step 2/3] Downloading real images from picsum.photos...")
    print(f"  Using {MAX_DOWNLOAD_WORKERS} parallel workers\n")
    image_map = download_images_parallel(items)

    # Update items with image paths
    success = 0
    for item in items:
        path = image_map.get(item["product_id"], "")
        item["image_path"] = path
        if path:
            success += 1

    print(f"\n  ✅ Downloaded {success}/{len(items)} images")

    # Step 3: Save CSV
    print(f"\n[Step 3/3] Saving to CSV...")
    fieldnames = [
        "product_id", "product_name", "category", "description",
        "price", "image_url", "image_path", "lost_item_description",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(items)

    print(f"  ✅ Saved {len(items)} products to {OUTPUT_CSV}")

    # Summary
    categories = set(item["category"] for item in items)
    cat_counts = {}
    for item in items:
        cat_counts[item["category"]] = cat_counts.get(item["category"], 0) + 1

    print(f"\n{'─' * 50}")
    print(f"📊 SUMMARY")
    print(f"{'─' * 50}")
    print(f"   Total items:  {len(items)}")
    print(f"   Images:       {success} real photos")
    print(f"   Categories:   {len(categories)}")
    for cat in sorted(cat_counts.keys()):
        print(f"     • {cat}: {cat_counts[cat]} items")
    print(f"\n   Sample: {items[0]['product_name']} ({items[0]['category']})")
    print(f"           \"{items[0]['lost_item_description'][:80]}...\"")


if __name__ == "__main__":
    main()
