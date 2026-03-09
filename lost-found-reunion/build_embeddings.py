"""
Phase 3: Embeddings + Vector Database
  - Text embeddings via sentence-transformers (all-MiniLM-L6-v2, 384-d)
  - Image embeddings via CLIP (openai/clip-vit-base-patch32, 512-d)
  - Combined (896-d) normalized embeddings
  - Stored in ChromaDB + pickled backup

Usage:
    python build_embeddings.py
"""

import os
import pickle
import numpy as np
import pandas as pd
from PIL import Image
from tqdm import tqdm
from sklearn.preprocessing import normalize

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "data")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "embeddings")
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
INPUT_CSV = os.path.join(DATA_DIR, "lost_found_dataset_cleaned.csv")
EMBEDDINGS_PKL = os.path.join(EMBEDDINGS_DIR, "lost_found_embeddings.pkl")

TEXT_MODEL_NAME = "all-MiniLM-L6-v2"
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
TEXT_DIM = 384
IMAGE_DIM = 512


# ---------------------------------------------------------------------------
# 1. Load text embedding model
# ---------------------------------------------------------------------------
def load_text_model():
    print("[Model] Loading sentence-transformers model...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer(TEXT_MODEL_NAME)
    print(f"[Model] Loaded '{TEXT_MODEL_NAME}' (output dim={TEXT_DIM})")
    return model


# ---------------------------------------------------------------------------
# 2. Load CLIP model
# ---------------------------------------------------------------------------
def load_clip_model():
    print("[Model] Loading CLIP model...")
    from transformers import CLIPModel, CLIPProcessor
    model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
    processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
    print(f"[Model] Loaded '{CLIP_MODEL_NAME}' (output dim={IMAGE_DIM})")
    return model, processor


# ---------------------------------------------------------------------------
# 3. Generate text embeddings
# ---------------------------------------------------------------------------
def generate_text_embeddings(text_model, texts: list[str]) -> np.ndarray:
    print(f"\n[Embeddings] Generating text embeddings for {len(texts)} items...")
    embeddings = text_model.encode(
        texts,
        show_progress_bar=True,
        batch_size=32,
        convert_to_numpy=True,
    )
    print(f"[Embeddings] Text embeddings shape: {embeddings.shape}")
    return embeddings


# ---------------------------------------------------------------------------
# 4. Generate image embeddings
# ---------------------------------------------------------------------------
def generate_image_embeddings(clip_model, clip_processor, image_paths: list[str]) -> np.ndarray:
    import torch
    print(f"\n[Embeddings] Generating image embeddings for {len(image_paths)} items...")
    embeddings = []

    for img_path in tqdm(image_paths, desc="Image embeddings"):
        full_path = os.path.join(BASE_DIR, img_path)
        try:
            image = Image.open(full_path).convert("RGB")
            inputs = clip_processor(images=image, return_tensors="pt")
            with torch.no_grad():
                image_features = clip_model.get_image_features(**inputs)
            # Normalize CLIP features
            image_features = image_features / image_features.norm(p=2, dim=-1, keepdim=True)
            embeddings.append(image_features.squeeze().numpy())
        except Exception as e:
            print(f"  ⚠ Failed to embed {img_path}: {e}")
            embeddings.append(np.zeros(IMAGE_DIM))

    result = np.array(embeddings)
    print(f"[Embeddings] Image embeddings shape: {result.shape}")
    return result


# ---------------------------------------------------------------------------
# 5. Combine + normalize
# ---------------------------------------------------------------------------
def combine_embeddings(text_emb: np.ndarray, image_emb: np.ndarray) -> np.ndarray:
    print(f"\n[Combine] Concatenating text ({text_emb.shape[1]}d) + image ({image_emb.shape[1]}d)...")
    combined = np.concatenate([text_emb, image_emb], axis=1)
    combined = normalize(combined, norm="l2")
    print(f"[Combine] Combined normalized shape: {combined.shape}")
    return combined


# ---------------------------------------------------------------------------
# 6. Store in ChromaDB
# ---------------------------------------------------------------------------
def store_in_chromadb(df: pd.DataFrame, embeddings: np.ndarray):
    import chromadb
    print(f"\n[ChromaDB] Storing {len(df)} items in collection 'lost_found_items'...")

    client = chromadb.PersistentClient(path=CHROMA_DIR)

    # Delete collection if it already exists (fresh rebuild)
    try:
        client.delete_collection("lost_found_items")
    except Exception:
        pass

    collection = client.create_collection(
        name="lost_found_items",
        metadata={"hnsw:space": "cosine"},
    )

    # ChromaDB expects lists
    ids = [str(row["product_id"]) for _, row in df.iterrows()]
    metadatas = [
        {
            "product_id": int(row["product_id"]),
            "product_name": str(row["product_name"]),
            "category": str(row["category"]),
            "image_path": str(row["image_path"]),
        }
        for _, row in df.iterrows()
    ]
    documents = [str(row.get("combined_text", "")) for _, row in df.iterrows()]

    # Add in batches (ChromaDB has a batch limit)
    batch_size = 40
    for i in tqdm(range(0, len(ids), batch_size), desc="ChromaDB insert"):
        end = min(i + batch_size, len(ids))
        collection.add(
            ids=ids[i:end],
            embeddings=embeddings[i:end].tolist(),
            metadatas=metadatas[i:end],
            documents=documents[i:end],
        )

    print(f"[ChromaDB] ✅ Stored {collection.count()} items in 'lost_found_items'")
    return collection


# ---------------------------------------------------------------------------
# 7. Save pickle backup
# ---------------------------------------------------------------------------
def save_pickle(df: pd.DataFrame, embeddings: np.ndarray):
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    data = {
        "product_ids": df["product_id"].tolist(),
        "product_names": df["product_name"].tolist(),
        "embeddings": embeddings,
    }
    with open(EMBEDDINGS_PKL, "wb") as f:
        pickle.dump(data, f)
    print(f"[Pickle] ✅ Saved embeddings to {EMBEDDINGS_PKL}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("  Phase 3: Embeddings + Vector Database")
    print("=" * 60)

    # Load cleaned data
    if not os.path.exists(INPUT_CSV):
        print(f"❌ Cleaned dataset not found: {INPUT_CSV}")
        print("   Run 'python clean_data.py' first.")
        return

    df = pd.read_csv(INPUT_CSV)
    print(f"\n[Data] Loaded {len(df)} items from {INPUT_CSV}")

    # Ensure directories
    os.makedirs(EMBEDDINGS_DIR, exist_ok=True)
    os.makedirs(CHROMA_DIR, exist_ok=True)

    # Load models
    text_model = load_text_model()
    clip_model, clip_processor = load_clip_model()

    # Generate embeddings
    texts = df["combined_text"].fillna("").tolist()
    image_paths = df["image_path"].fillna("").tolist()

    text_embeddings = generate_text_embeddings(text_model, texts)
    image_embeddings = generate_image_embeddings(clip_model, clip_processor, image_paths)

    # Combine and normalize
    combined = combine_embeddings(text_embeddings, image_embeddings)

    # Store
    store_in_chromadb(df, combined)
    save_pickle(df, combined)

    print(f"\n{'=' * 60}")
    print(f"  ✅ Stored {len(df)} items in ChromaDB + pickle")
    print(f"     Text dim: {TEXT_DIM}  |  Image dim: {IMAGE_DIM}  |  Combined: {combined.shape[1]}")
    print(f"{'=' * 60}\n")


if __name__ == "__main__":
    main()
