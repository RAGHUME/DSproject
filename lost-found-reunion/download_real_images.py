"""
Download REAL product images using DuckDuckGo image search.
No API key needed. Maps each product to a search keyword and
downloads the first matching image.

Usage:
    pip install duckduckgo-search
    python download_real_images.py
"""

import os
import csv
import time
import hashlib
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
DATA_DIR = os.path.join(BASE_DIR, "data")
INPUT_CSV = os.path.join(DATA_DIR, "scraped_products.csv")
IMAGE_SIZE = 300
MAX_WORKERS = 5  # keep low to avoid rate limits

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# Search keyword mapping — maps product names to image search queries
# This gives much better results than searching the full product name
# ---------------------------------------------------------------------------
KEYWORD_MAP = {
    # Electronics
    "Wireless Headphones": "wireless headphones product photo",
    "AirPods": "apple airpods white case",
    "Galaxy Buds": "samsung galaxy buds earbuds",
    "Portable Speaker": "portable bluetooth speaker",
    "Power Bank": "portable power bank charger",
    "Wireless Mouse": "wireless computer mouse",
    "USB Flash Drive": "usb flash drive pendrive",
    "Scientific Calculator": "scientific calculator casio",
    "Laptop Charger": "laptop charger adapter",
    "SoundLink": "bose bluetooth speaker small",
    "Fitness Tracker": "fitness band tracker watch",
    "Kindle": "kindle ereader device",
    "Keyboard": "computer keyboard wired",
    "EarPods": "apple wired earphones white",
    "WiFi Router": "portable wifi router device",
    "Desktop Speakers": "small desktop computer speakers",
    "USB-C Hub": "usb c hub adapter multiport",
    "Boat Rockerz": "wireless on ear headphones",

    # Bags
    "Backpack": "school backpack bag",
    "Duffel Bag": "gym duffel bag sports",
    "Kanken": "fjallraven kanken backpack",
    "Sackpack": "drawstring sackpack bag",
    "Messenger Bag": "laptop messenger bag",
    "Lunch Bag": "insulated lunch bag",
    "Laptop Backpack": "laptop backpack bag",
    "Sling Bag": "crossbody sling bag",
    "Daypack": "small daypack backpack",
    "Belt Bag": "belt bag fanny pack",
    "Sports Bag": "sports gym bag",
    "Crossbody Bag": "small crossbody purse bag",
    "Canvas Backpack": "canvas backpack casual",
    "Tactical Backpack": "tactical military backpack",
    "Travel Backpack": "travel backpack large",

    # Clothing
    "Puffer Jacket": "puffer jacket black",
    "Jeans": "blue denim jeans",
    "Hoodie": "grey pullover hoodie",
    "Running Shoes": "running shoes sneakers",
    "Sunglasses": "black sunglasses classic",
    "T-Shirt": "sports t-shirt dryfit",
    "Sun Hat": "wide brim sun hat",
    "Track Pants": "black track pants joggers",
    "Down Vest": "lightweight down vest",
    "Clogs": "crocs clogs shoes",
    "Leather Belt": "brown leather belt men",
    "Running Shorts": "running shorts athletic",
    "Denim Jacket": "blue denim jacket",
    "Sneakers": "classic retro sneakers",
    "Blazer": "oversized blazer jacket",
    "Chinos": "khaki chino pants",
    "Polo T-Shirt": "polo tshirt collar",
    "Formal Shirt": "white formal shirt",

    # Books
    "Calculus": "calculus textbook mathematics",
    "Algorithms": "algorithms textbook CLRS",
    "Gatsby": "great gatsby book cover",
    "Chemistry": "organic chemistry textbook",
    "Psychology": "psychology textbook book",
    "Notebook": "moleskine notebook black",
    "Harry Potter": "harry potter book paperback",
    "Engineering Mechanics": "engineering mechanics textbook",
    "Digital Logic": "digital logic design textbook",
    "Let Us C": "c programming book",
    "Sapiens": "sapiens book yuval harari",
    "Atomic Habits": "atomic habits book james clear",
    "Dictionary": "oxford english dictionary book",
    "Data Structures": "data structures textbook",
    "Rich Dad": "rich dad poor dad book",
    "Alchemist": "alchemist book paulo coelho",
    "Clean Code": "clean code book programming",
    "Art of War": "art of war book sun tzu",
    "Operating System": "operating system concepts textbook",
    "Thinking Fast": "thinking fast and slow book",

    # Accessories
    "Water Bottle": "stainless steel water bottle",
    "Apple Watch": "apple watch smartwatch",
    "Chronograph Watch": "leather strap chronograph watch",
    "Holbrook": "oakley sports sunglasses",
    "Bluetooth Tracker": "tile bluetooth tracker keys",
    "USB-C Cable": "braided usb c charging cable",
    "Nalgene": "nalgene water bottle transparent",
    "Wired Earphones": "wired earphones with mic",
    "Aviator": "aviator sunglasses gold frame",
    "Flask": "stainless steel thermos flask",
    "Wired Earbuds": "in ear wired earbuds",
    "Digital Watch": "casio retro digital watch",
    "Umbrella": "compact folding umbrella",
    "Steel Water Bottle": "steel water bottle blue",
    "Wallet": "trifold wallet men",
    "Smartwatch": "smartwatch fitness square dial",
    "Women's Watch": "women analog watch bracelet",
    "Neckband": "bluetooth neckband earphones",
    "Ballpoint Pen": "cross chrome ballpoint pen",

    # Sports Equipment
    "Basketball": "basketball orange ball",
    "Badminton Racket": "badminton racket yonex",
    "Swim Goggles": "swimming goggles clear",
    "Soccer Ball": "soccer football white",
    "Yoga Mat": "yoga mat black rolled",
    "Golf Club": "golf clubs set bag",
    "Boxing Gloves": "red boxing gloves training",
    "Cricket Bat": "cricket bat willow",
    "Football": "football soccer ball yellow",
    "Yoga Block": "yoga block foam purple",
    "Table Tennis": "table tennis paddle bat",
    "Tennis Ball": "tennis balls yellow pack",
    "Wrist Support": "wrist support band gym",
    "Cricket Gloves": "cricket batting gloves white",
    "Champions League Ball": "football champions league ball",
    "Tennis Racket": "tennis racket head",
    "Cricket Helmet": "cricket helmet with grill",
    "Football Boots": "football boots cleats",

    # Stationery
    "iPad": "ipad tablet with pencil",
    "Fineliner": "staedtler fineliner pen set colors",
    "TI-84": "graphing calculator ti84",
    "Spiral Notebook": "spiral notebook college ruled",
    "Gel Pen": "gel pen set colorful",
    "Sticky Notes": "post it sticky notes neon",
    "Stapler": "red desktop stapler metal",
    "Geometry Box": "geometry box compass set",
    "Fountain Pen": "fountain pen black parker",
    "Ball Pen": "ball pen set blue",
    "Colour Pencils": "colored pencils tin box",
    "WhiteBoard Markers": "whiteboard markers set",
    "Ruler": "transparent plastic ruler 30cm",
    "Pilot V7": "pilot pen fine tip",
    "Packaging Tape": "packing tape dispenser clear",
    "Paper Punch": "2 hole paper punch",
    "Pencils": "graphite pencils HB pack",
    "Portfolio Folder": "executive portfolio folder leather",
}


def get_search_keyword(product_name: str) -> str:
    """Find the best matching search keyword for a product name."""
    # Check for keyword matches (longest match first)
    best_match = None
    best_length = 0
    for key, query in KEYWORD_MAP.items():
        if key.lower() in product_name.lower() and len(key) > best_length:
            best_match = query
            best_length = len(key)
    if best_match:
        return best_match
    # Fallback: use the product name itself
    return product_name + " product"


def search_and_download_image(product_id: int, product_name: str, category: str) -> str:
    """Search for a product image using DuckDuckGo and download it."""
    filename = f"product_{product_id:03d}.jpg"
    filepath = os.path.join(IMAGES_DIR, filename)

    # Skip if already downloaded
    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return os.path.join("images", filename)

    keyword = get_search_keyword(product_name)

    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.images(
                keywords=keyword,
                max_results=5,
                size="Medium",
                type_image="photo",
            ))

        if not results:
            return ""

        # Try downloading the first few results until one works
        for result in results[:5]:
            img_url = result.get("image", "")
            if not img_url:
                continue
            try:
                resp = requests.get(img_url, headers=HEADERS, timeout=15, stream=True)
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                if "image" not in content_type:
                    continue

                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)

                # Verify it's a valid image and resize
                from PIL import Image
                img = Image.open(filepath)
                img = img.convert("RGB")
                img = img.resize((IMAGE_SIZE, IMAGE_SIZE), Image.LANCZOS)
                img.save(filepath, "JPEG", quality=85)
                return os.path.join("images", filename)
            except Exception:
                continue

    except Exception as e:
        pass

    return ""


def main():
    print("=" * 60)
    print("  Download Real Product Images")
    print("  Using DuckDuckGo Image Search (no API key needed)")
    print("=" * 60)

    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Load product data
    if not os.path.exists(INPUT_CSV):
        print(f"❌ CSV not found: {INPUT_CSV}")
        print("   Run 'python create_sample_data.py' first.")
        return

    products = []
    with open(INPUT_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            products.append(row)

    print(f"\n[Info] Found {len(products)} products")
    print(f"[Info] Using {MAX_WORKERS} parallel workers")
    print(f"[Info] Images will be saved to {IMAGES_DIR}/\n")

    # Group products by base name to avoid duplicate searches
    # Products with variations (e.g., "Sony Headphones (Renewed)") share the same base
    base_keywords = {}
    for p in products:
        name = p["product_name"]
        # Strip variation suffixes
        base_name = name.split(" (")[0].split(" - ")[0].split(" v2")[0].strip()
        keyword = get_search_keyword(base_name)
        base_keywords[name] = keyword

    unique_keywords = set(base_keywords.values())
    print(f"[Info] {len(unique_keywords)} unique search queries for {len(products)} products\n")

    # Download images
    success = 0
    failed = 0
    updated_products = []

    # Process sequentially with small delays to avoid rate limiting
    for product in tqdm(products, desc="Downloading real images"):
        pid = int(product["product_id"])
        name = product["product_name"]
        cat = product.get("category", "")

        path = search_and_download_image(pid, name, cat)
        product["image_path"] = path

        if path:
            success += 1
        else:
            failed += 1

        updated_products.append(product)
        time.sleep(0.3)  # Small delay to avoid rate limiting

    # Update the CSV with new image paths
    fieldnames = list(products[0].keys())
    with open(INPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(updated_products)

    print(f"\n{'─' * 50}")
    print(f"📊 DOWNLOAD SUMMARY")
    print(f"{'─' * 50}")
    print(f"   ✅ Downloaded: {success}/{len(products)} images")
    if failed:
        print(f"   ❌ Failed: {failed} (will use placeholder)")
    print(f"   📁 Saved to: {IMAGES_DIR}/")
    print(f"   📄 Updated: {INPUT_CSV}")
    print(f"\n   Next step: python clean_data.py")


if __name__ == "__main__":
    main()
