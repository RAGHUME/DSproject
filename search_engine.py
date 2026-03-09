"""
Core search logic — importable module used by app.py.

Provides:
  - embed_text_query(query)   → 384-d numpy array
  - embed_image_query(image)  → 512-d numpy array
  - search(query_text, query_image=None, top_k=5) → list[dict]
  - get_ai_explanation(query, product_name, description) → str

Uses xAI Grok API for AI explanations.
"""

import os
import numpy as np
from PIL import Image
from sklearn.preprocessing import normalize

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(__file__)
CHROMA_DIR = os.path.join(BASE_DIR, "chroma_db")
TEXT_MODEL_NAME = "all-MiniLM-L6-v2"
CLIP_MODEL_NAME = "openai/clip-vit-base-patch32"
TEXT_DIM = 384
IMAGE_DIM = 512

# ---------------------------------------------------------------------------
# Lazy-loaded singletons (loaded once, reused across calls)
# ---------------------------------------------------------------------------
_text_model = None
_clip_model = None
_clip_processor = None
_chroma_collection = None


def _get_text_model():
    global _text_model
    if _text_model is None:
        from sentence_transformers import SentenceTransformer
        _text_model = SentenceTransformer(TEXT_MODEL_NAME)
    return _text_model


def _get_clip_model():
    global _clip_model, _clip_processor
    if _clip_model is None:
        from transformers import CLIPModel, CLIPProcessor
        _clip_model = CLIPModel.from_pretrained(CLIP_MODEL_NAME)
        _clip_processor = CLIPProcessor.from_pretrained(CLIP_MODEL_NAME)
    return _clip_model, _clip_processor


def _get_chroma_collection():
    global _chroma_collection
    if _chroma_collection is None:
        import chromadb
        import traceback
        try:
            client = chromadb.PersistentClient(path=CHROMA_DIR)
            _chroma_collection = client.get_collection("lost_found_items")
        except Exception as e:
            print(f"[ChromaDB ERROR] Failed to load collection: {e}")
            traceback.print_exc()
            raise RuntimeError(
                f"Could not load ChromaDB collection from '{CHROMA_DIR}'. "
                f"Make sure you've run 'python build_embeddings.py' first. "
                f"Error: {e}"
            )
    return _chroma_collection


# ---------------------------------------------------------------------------
# Embedding functions
# ---------------------------------------------------------------------------

def embed_text_query(query: str) -> np.ndarray:
    """Embed a text query → 384-d vector."""
    model = _get_text_model()
    embedding = model.encode([query], convert_to_numpy=True)
    return embedding[0]  # shape (384,)


def embed_image_query(image: Image.Image) -> np.ndarray:
    """Embed a PIL Image → 512-d vector."""
    import torch
    import torch.nn.functional as F
    model, processor = _get_clip_model()
    inputs = processor(images=image.convert("RGB"), return_tensors="pt")
    with torch.no_grad():
        features = model.get_image_features(**inputs)
    # Handle both tensor and BaseModelOutputWithPooling
    if hasattr(features, "pooler_output"):
        features = features.pooler_output
    elif hasattr(features, "last_hidden_state"):
        features = features.last_hidden_state[:, 0, :]
    features = F.normalize(features, p=2, dim=-1)
    return features.squeeze().cpu().numpy()  # shape (512,)


# ---------------------------------------------------------------------------
# Combined query embedding
# ---------------------------------------------------------------------------

def _build_query_embedding(query_text: str | None, query_image: Image.Image | None) -> list[float]:
    """
    Build a combined (text + image) query embedding of 896-d.
    If one modality is missing, pad with zeros.
    """
    if query_text:
        text_emb = embed_text_query(query_text)
    else:
        text_emb = np.zeros(TEXT_DIM)

    if query_image is not None:
        image_emb = embed_image_query(query_image)
    else:
        image_emb = np.zeros(IMAGE_DIM)

    combined = np.concatenate([text_emb, image_emb])
    combined = normalize(combined.reshape(1, -1), norm="l2").flatten()
    return combined.tolist()


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------

def search(query_text: str | None = None,
           query_image: Image.Image | None = None,
           top_k: int = 5) -> list[dict]:
    """
    Search ChromaDB for the top-k nearest items.

    Returns a list of dicts with keys:
      product_id, product_name, category, image_path, score, document
    """
    if not query_text and query_image is None:
        return []

    query_embedding = _build_query_embedding(query_text, query_image)
    collection = _get_chroma_collection()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        include=["metadatas", "documents", "distances"],
    )

    items = []
    if results and results["ids"] and results["ids"][0]:
        for i, _id in enumerate(results["ids"][0]):
            meta = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            # ChromaDB cosine distance → similarity score (0-100%)
            score = max(0.0, (1.0 - distance)) * 100
            items.append({
                "product_id": meta.get("product_id", _id),
                "product_name": meta.get("product_name", "Unknown"),
                "category": meta.get("category", ""),
                "image_path": meta.get("image_path", ""),
                "score": round(score, 1),
                "document": results["documents"][0][i] if results["documents"] else "",
            })

    return items


# ---------------------------------------------------------------------------
# AI Explanation via Grok (xAI)
# ---------------------------------------------------------------------------

def get_ai_explanation(query: str, product_name: str, description: str) -> str:
    """
    Call xAI Grok API to explain why this item might match the student's query.
    Returns a 2-sentence explanation string.
    """
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        return (
            f"This item '{product_name}' may match your description based on "
            f"semantic similarity. Please check the image and details to confirm."
        )

    try:
        from openai import OpenAI

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.x.ai/v1",
        )

        prompt = (
            f"A student lost an item and described it as: \"{query}\".\n"
            f"A potential match found is: {product_name} — {description}.\n\n"
            f"In exactly 2 sentences, explain why this could be a match and "
            f"what the student should check to confirm. Be helpful and concise."
        )

        response = client.chat.completions.create(
            model="grok-3-mini-fast",
            messages=[
                {"role": "system", "content": "You are a helpful lost-and-found assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=150,
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return (
            f"This item '{product_name}' may match your description based on "
            f"semantic similarity. (AI explanation unavailable: {e})"
        )
