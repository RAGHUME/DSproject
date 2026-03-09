"""
Phase 1: Data Sourcing — Scrape products from scrapeme.live/shop/
and generate "lost item descriptions" using xAI Grok API.

Usage:
    set XAI_API_KEY=your-api-key
    python scrape_data.py
"""

import os
import re
import csv
import time
import requests
from bs4 import BeautifulSoup
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_URL = "https://scrapeme.live/shop/"
IMAGES_DIR = os.path.join(os.path.dirname(__file__), "images")
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
OUTPUT_CSV = os.path.join(DATA_DIR, "scraped_products.csv")
MAX_PAGES = 5  # Each page has ~16 products → up to ~80; site has 48 pages
TARGET_COUNT = 150  # stop early once we have enough

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def ensure_dirs():
    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)


def scrape_product_links() -> list[str]:
    """Collect individual product page URLs across paginated listing pages."""
    links = []
    page = 1
    while page <= 48:  # site has 48 pages max
        url = BASE_URL if page == 1 else f"{BASE_URL}page/{page}/"
        print(f"[Scraping] Listing page {page}: {url}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            resp.raise_for_status()
        except requests.RequestException as e:
            print(f"  ⚠ Failed to fetch page {page}: {e}")
            break

        soup = BeautifulSoup(resp.text, "lxml")
        products = soup.select("ul.products li.product a.woocommerce-LoopProduct-link")
        if not products:
            break

        for a_tag in products:
            href = a_tag.get("href")
            if href and href not in links:
                links.append(href)

        if len(links) >= TARGET_COUNT:
            break
        page += 1
        time.sleep(0.5)

    print(f"[Scraping] Collected {len(links)} product links.\n")
    return links[:TARGET_COUNT]


def scrape_product_detail(url: str) -> dict | None:
    """Scrape a single product detail page."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
    except requests.RequestException as e:
        print(f"  ⚠ Failed: {url} — {e}")
        return None

    soup = BeautifulSoup(resp.text, "lxml")

    name_tag = soup.select_one("h1.product_title")
    product_name = name_tag.get_text(strip=True) if name_tag else ""

    cat_tag = soup.select_one("span.posted_in a")
    category = cat_tag.get_text(strip=True) if cat_tag else "Uncategorized"

    desc_tag = soup.select_one("div.woocommerce-product-details__short-description")
    if not desc_tag:
        desc_tag = soup.select_one("div#tab-description")
    description = desc_tag.get_text(" ", strip=True) if desc_tag else ""

    price_tag = soup.select_one("p.price span.amount, p.price ins span.amount")
    price = price_tag.get_text(strip=True) if price_tag else "0.00"
    # Clean price to just digits + decimal
    price = re.sub(r"[^\d.]", "", price)

    img_tag = soup.select_one("div.woocommerce-product-gallery__image img")
    image_url = ""
    if img_tag:
        image_url = img_tag.get("src") or img_tag.get("data-src") or ""

    return {
        "product_name": product_name,
        "category": category,
        "description": description,
        "price": price,
        "image_url": image_url,
    }


def download_image(image_url: str, product_id: int) -> str:
    """Download an image and return the local path."""
    filename = f"product_{product_id:03d}.jpg"
    filepath = os.path.join(IMAGES_DIR, filename)
    if os.path.exists(filepath):
        return os.path.join("images", filename)
    try:
        resp = requests.get(image_url, headers=HEADERS, timeout=15, stream=True)
        resp.raise_for_status()
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(8192):
                f.write(chunk)
    except requests.RequestException as e:
        print(f"  ⚠ Image download failed for product {product_id}: {e}")
        return ""
    return os.path.join("images", filename)


def generate_lost_description(product_name: str, description: str, category: str) -> str:
    """Use xAI Grok API to generate a realistic 'lost item' student description."""
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        # Fallback: simple template
        return f"I lost something that looks like a {product_name}. It was {category}."

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )

        prompt = (
            f"A student lost an item. The actual product is:\n"
            f"Name: {product_name}\nCategory: {category}\nDescription: {description}\n\n"
            f"Write a 1-2 sentence description AS IF a confused college student is "
            f"describing the item they lost WITHOUT knowing the exact product name. "
            f"Be vague, use colloquial language, mention where on campus they might "
            f"have lost it (library, cafeteria, gym, lecture hall, bus stop, etc.). "
            f"Do NOT mention the exact brand or product name."
        )

        response = client.chat.completions.create(
            model="grok-3-mini-fast",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"  ⚠ Grok API error: {e}")
        return f"I lost something that looks like a {product_name}. It was {category}."


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  Phase 1: Data Sourcing — Scrape + Generate Dataset")
    print("=" * 60)

    ensure_dirs()

    # Step 1: Scrape product links
    product_links = scrape_product_links()
    if not product_links:
        print("❌ No product links found. Check your internet connection.")
        print("   Tip: Run 'python create_sample_data.py' instead.")
        return

    # Step 2: Scrape details + download images + generate descriptions
    rows = []
    print("[Processing] Scraping details, downloading images, generating descriptions...\n")
    for idx, link in enumerate(tqdm(product_links, desc="Products"), start=1):
        detail = scrape_product_detail(link)
        if not detail or not detail["product_name"]:
            continue

        # Download image
        image_path = ""
        if detail["image_url"]:
            image_path = download_image(detail["image_url"], idx)

        # Generate lost description
        lost_desc = generate_lost_description(
            detail["product_name"], detail["description"], detail["category"]
        )

        rows.append({
            "product_id": idx,
            "product_name": detail["product_name"],
            "category": detail["category"],
            "description": detail["description"],
            "price": detail["price"],
            "image_url": detail["image_url"],
            "image_path": image_path,
            "lost_item_description": lost_desc,
        })

        time.sleep(0.3)  # polite delay

    # Step 3: Save to CSV
    if not rows:
        print("❌ No products scraped successfully.")
        return

    fieldnames = [
        "product_id", "product_name", "category", "description",
        "price", "image_url", "image_path", "lost_item_description",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Saved {len(rows)} products to {OUTPUT_CSV}")
    print(f"✅ Images saved to {IMAGES_DIR}/")
    print(f"\nSample row:\n  {rows[0]}")


if __name__ == "__main__":
    main()
