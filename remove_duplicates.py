"""Remove duplicate images from the images folder based on file content hash."""
import os
import hashlib

IMAGES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")

def get_file_hash(filepath):
    h = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def main():
    files = sorted([f for f in os.listdir(IMAGES_DIR) if f.endswith((".jpg", ".png", ".jpeg"))])
    print(f"Total images: {len(files)}")

    seen_hashes = {}  # hash -> first filename
    duplicates = []

    for fname in files:
        fpath = os.path.join(IMAGES_DIR, fname)
        fhash = get_file_hash(fpath)
        if fhash in seen_hashes:
            duplicates.append((fname, seen_hashes[fhash]))
        else:
            seen_hashes[fhash] = fname

    print(f"Unique images: {len(seen_hashes)}")
    print(f"Duplicates found: {len(duplicates)}")

    if duplicates:
        for dup, original in duplicates:
            os.remove(os.path.join(IMAGES_DIR, dup))
        print(f"\n✅ Removed {len(duplicates)} duplicate images")
        print(f"   Remaining: {len(seen_hashes)} unique images")
    else:
        print("\n✅ No duplicates found!")

if __name__ == "__main__":
    main()
