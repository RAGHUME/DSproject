"""
Phase 2: Data Preparation — Clean and standardize the scraped dataset.

Usage:
    python clean_data.py
"""

import os
import pandas as pd

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
INPUT_CSV = os.path.join(DATA_DIR, "scraped_products.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "lost_found_dataset_cleaned.csv")


def main():
    print("=" * 60)
    print("  Phase 2: Data Preparation — Clean the Dataset")
    print("=" * 60)

    # -----------------------------------------------------------------------
    # 1. Load data
    # -----------------------------------------------------------------------
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Input file not found: {INPUT_CSV}")
        print("   Run 'python scrape_data.py' or 'python create_sample_data.py' first.")
        return

    df = pd.read_csv(INPUT_CSV)
    print(f"\n[Loaded] {len(df)} rows from {INPUT_CSV}")

    # -----------------------------------------------------------------------
    # 2. Drop rows with missing product_name (keep items without images)
    # -----------------------------------------------------------------------
    before = len(df)
    df = df.dropna(subset=["product_name"])
    df = df[df["product_name"].str.strip() != ""]
    dropped = before - len(df)
    if dropped:
        print(f"[Clean]  Dropped {dropped} rows with missing product_name")

    # Fill missing image paths with empty string (will show placeholder in UI)
    df["image_path"] = df["image_path"].fillna("")
    has_image = (df["image_path"].str.strip() != "").sum()
    print(f"[Clean]  {has_image}/{len(df)} items have real images ({len(df) - has_image} will use placeholder)")

    # -----------------------------------------------------------------------
    # 3. Remove duplicate product names
    # -----------------------------------------------------------------------
    before = len(df)
    df = df.drop_duplicates(subset=["product_name"], keep="first")
    dupes = before - len(df)
    if dupes:
        print(f"[Clean]  Removed {dupes} duplicate product names")

    # -----------------------------------------------------------------------
    # 4. Standardize category names (title case, strip whitespace)
    # -----------------------------------------------------------------------
    df["category"] = df["category"].astype(str).str.strip().str.title()
    print(f"[Clean]  Standardized category names to title case")

    # -----------------------------------------------------------------------
    # 5. Fill missing text columns with empty strings
    # -----------------------------------------------------------------------
    for col in ["description", "lost_item_description"]:
        df[col] = df[col].fillna("")

    # -----------------------------------------------------------------------
    # 6. Create combined_text column
    # -----------------------------------------------------------------------
    df["combined_text"] = (
        df["product_name"].astype(str) + " " +
        df["category"].astype(str) + " " +
        df["description"].astype(str) + " " +
        df["lost_item_description"].astype(str)
    )
    print(f"[Clean]  Created 'combined_text' column")

    # -----------------------------------------------------------------------
    # 7. Reset index
    # -----------------------------------------------------------------------
    df = df.reset_index(drop=True)
    df["product_id"] = range(1, len(df) + 1)

    # -----------------------------------------------------------------------
    # 8. Save cleaned dataset
    # -----------------------------------------------------------------------
    df.to_csv(OUTPUT_CSV, index=False)
    print(f"\n✅ Saved cleaned dataset to {OUTPUT_CSV}")

    # -----------------------------------------------------------------------
    # 9. Print summary
    # -----------------------------------------------------------------------
    categories = df["category"].unique()
    print(f"\n{'─' * 50}")
    print(f"📊 DATASET SUMMARY")
    print(f"{'─' * 50}")
    print(f"   Total items:       {len(df)}")
    print(f"   Unique categories: {len(categories)}")
    print(f"   Categories:        {', '.join(sorted(categories))}")
    print(f"\n   Columns: {list(df.columns)}")
    print(f"\n   Sample rows (first 3):")
    print(df[["product_id", "product_name", "category", "combined_text"]].head(3).to_string(index=False))
    print()


if __name__ == "__main__":
    main()
