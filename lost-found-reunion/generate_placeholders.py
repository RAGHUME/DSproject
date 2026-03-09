"""
Generate placeholder product images for items missing real photos.
Creates clean dark-themed cards with category icon + product name.

Usage:
    python generate_placeholders.py
"""

import os
import csv
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
DATA_DIR = os.path.join(BASE_DIR, "data")
CSV_FILE = os.path.join(DATA_DIR, "scraped_products.csv")
SIZE = 300

# Category → (background color, accent color, emoji label)
CATEGORY_STYLES = {
    "Electronics":              ("#1a1f2e", "#667eea", "ELECTRONICS"),
    "Bags":                     ("#1a1f2e", "#f093fb", "BAGS"),
    "Clothing":                 ("#1a1f2e", "#43e97b", "CLOTHING"),
    "Books":                    ("#1a1f2e", "#f7971e", "BOOKS"),
    "Accessories":              ("#1a1f2e", "#38f9d7", "ACCESSORIES"),
    "Sports Equipment":         ("#1a1f2e", "#e74c6f", "SPORTS"),
    "Stationery":               ("#1a1f2e", "#a18cd1", "STATIONERY"),
    "Smartphones":              ("#1a1f2e", "#5b86e5", "SMARTPHONES"),
    "Audio & Headphones":       ("#1a1f2e", "#fc5c7d", "AUDIO"),
    "Laptops":                  ("#1a1f2e", "#6a82fb", "LAPTOPS"),
    "Smartwatches":             ("#1a1f2e", "#00c9ff", "SMARTWATCHES"),
    "Cameras":                  ("#1a1f2e", "#f5af19", "CAMERAS"),
    "Cricket & Badminton Sports":("#1a1f2e", "#11998e", "SPORTS"),
    "Musical Instruments":      ("#1a1f2e", "#fc4a1a", "MUSIC"),
    "Gaming Accessories":       ("#1a1f2e", "#7f00ff", "GAMING"),
    "Mobile Accessories":       ("#1a1f2e", "#00b4db", "MOBILE"),
    "Stationery & Calculators": ("#1a1f2e", "#a18cd1", "STATIONERY"),
}
DEFAULT_STYLE = ("#1a1f2e", "#667eea", "ITEM")


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))


def create_placeholder(product_name, category, filepath):
    """Create a dark-themed placeholder image with product name."""
    bg_hex, accent_hex, label = CATEGORY_STYLES.get(category, DEFAULT_STYLE)
    bg = hex_to_rgb(bg_hex)
    accent = hex_to_rgb(accent_hex)

    img = Image.new("RGB", (SIZE, SIZE), bg)
    draw = ImageDraw.Draw(img)

    # Draw accent stripe at top
    draw.rectangle([0, 0, SIZE, 6], fill=accent)

    # Draw subtle border
    draw.rectangle([0, 0, SIZE-1, SIZE-1], outline=(*accent, 60), width=1)

    # Category label
    try:
        font_label = ImageFont.truetype("arial.ttf", 14)
        font_name = ImageFont.truetype("arial.ttf", 16)
        font_small = ImageFont.truetype("arial.ttf", 11)
    except (IOError, OSError):
        font_label = ImageFont.load_default()
        font_name = font_label
        font_small = font_label

    # Category badge
    label_w = draw.textlength(label, font=font_label) if hasattr(draw, 'textlength') else len(label) * 8
    badge_x = (SIZE - label_w) // 2 - 10
    badge_y = 30
    draw.rounded_rectangle(
        [badge_x, badge_y, badge_x + label_w + 20, badge_y + 26],
        radius=13, fill=(*accent, 40), outline=accent
    )
    draw.text(
        (badge_x + 10, badge_y + 5), label, fill=accent, font=font_label
    )

    # Product name (wrap text)
    name = product_name[:60]
    words = name.split()
    lines = []
    current = ""
    for w in words:
        test = f"{current} {w}".strip()
        tw = draw.textlength(test, font=font_name) if hasattr(draw, 'textlength') else len(test) * 9
        if tw < SIZE - 40:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)

    y_start = (SIZE // 2) - (len(lines) * 22 // 2)
    for line in lines[:4]:
        tw = draw.textlength(line, font=font_name) if hasattr(draw, 'textlength') else len(line) * 9
        x = (SIZE - tw) // 2
        draw.text((x, y_start), line, fill=(224, 224, 224), font=font_name)
        y_start += 22

    # "Lost & Found" at bottom
    bottom_text = "Lost & Found Reunion"
    btw = draw.textlength(bottom_text, font=font_small) if hasattr(draw, 'textlength') else len(bottom_text) * 7
    draw.text(((SIZE - btw) // 2, SIZE - 30), bottom_text, fill=(100, 104, 130), font=font_small)

    img.save(filepath, "JPEG", quality=90)


def main():
    print("=" * 50)
    print("  Generate Placeholder Images for Missing Products")
    print("=" * 50)

    os.makedirs(IMAGES_DIR, exist_ok=True)

    # Read CSV
    rows = []
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    print(f"\nTotal products: {len(rows)}")

    generated = 0
    updated = 0
    for row in rows:
        pid = row["product_id"]
        name = row["product_name"]
        cat = row.get("category", "")

        # Determine expected filename
        try:
            pid_int = int(pid)
        except ValueError:
            continue

        # Check both 3-digit and 4-digit formats
        fname3 = f"product_{pid_int:03d}.jpg"
        fname4 = f"product_{pid_int:04d}.jpg"
        path3 = os.path.join(IMAGES_DIR, fname3)
        path4 = os.path.join(IMAGES_DIR, fname4)

        # If real image exists, make sure CSV points to it
        if os.path.exists(path3) and os.path.getsize(path3) > 500:
            if row["image_path"] != os.path.join("images", fname3):
                row["image_path"] = os.path.join("images", fname3)
                updated += 1
            continue
        if os.path.exists(path4) and os.path.getsize(path4) > 500:
            if row["image_path"] != os.path.join("images", fname4):
                row["image_path"] = os.path.join("images", fname4)
                updated += 1
            continue

        # No image exists — generate placeholder
        target = path3 if pid_int < 1000 else path4
        target_rel = os.path.join("images", fname3 if pid_int < 1000 else fname4)
        create_placeholder(name, cat, target)
        row["image_path"] = target_rel
        generated += 1
        updated += 1

    # Save updated CSV
    fieldnames = list(rows[0].keys())
    with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\n✅ Generated {generated} placeholder images")
    print(f"✅ Updated {updated} image paths in CSV")
    print(f"\n   Next steps:")
    print(f"     python clean_data.py")
    print(f"     python build_embeddings.py")


if __name__ == "__main__":
    main()
