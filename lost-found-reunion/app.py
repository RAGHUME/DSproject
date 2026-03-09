"""
Phase 4: Streamlit UI — Lost & Found Reunion
Multi-modal semantic search for lost items.
Premium dark-theme UI with responsive design.

Usage:
    streamlit run app.py
"""

import os
import sys
import streamlit as st
from PIL import Image

# Ensure project root is on the path so imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from search_engine import search, get_ai_explanation

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Lost & Found Reunion — BLDEACET",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Dark glassmorphism theme
# ---------------------------------------------------------------------------
st.markdown("""
<style>
    /* ===== Google Fonts ===== */
    /* Uses Streamlit default font (Source Sans Pro) */

    /* ===== Dark Background ===== */
    .stApp {
        background: #0e1117 !important;
    }
    .main .block-container {
        padding-top: 1.5rem;
        max-width: 1200px;
    }

    /* ===== Hero Header Banner ===== */
    .hero-banner {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        padding: 2.5rem 2rem;
        border-radius: 20px;
        color: white;
        text-align: left;
        margin-bottom: 1.5rem;
        box-shadow: 0 12px 40px rgba(102, 126, 234, 0.25);
        position: relative;
        overflow: hidden;
    }
    .hero-banner::before {
        content: '';
        position: absolute;
        top: -50%;
        right: -20%;
        width: 400px;
        height: 400px;
        background: radial-gradient(circle, rgba(255,255,255,0.08) 0%, transparent 70%);
        border-radius: 50%;
    }
    .hero-banner h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 700;
        line-height: 1.2;
        position: relative;
        z-index: 1;
    }
    .hero-banner .hero-icon {
        font-size: 2rem;
        margin-right: 0.5rem;
        vertical-align: middle;
    }
    .hero-banner p {
        margin: 0.8rem 0 0;
        opacity: 0.85;
        font-size: 1rem;
        font-weight: 400;
        position: relative;
        z-index: 1;
        max-width: 600px;
    }

    /* ===== Stat Cards ===== */
    .stat-card {
        background: #1a1f2e;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 1.2rem 1rem;
        text-align: center;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.3);
    }
    .stat-icon {
        font-size: 1.2rem;
        margin-bottom: 0.3rem;
        opacity: 0.7;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea, #764ba2);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0;
        line-height: 1.2;
    }
    .stat-label {
        font-size: 0.8rem;
        color: #8b8fa3;
        font-weight: 500;
        margin-top: 0.2rem;
    }

    /* ===== Result Card ===== */
    .result-card {
        background: #1a1f2e;
        border: 1px solid rgba(255,255,255,0.06);
        border-radius: 14px;
        padding: 1.2rem;
        margin-bottom: 0.8rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .result-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 8px 24px rgba(0,0,0,0.3);
        border-color: rgba(102, 126, 234, 0.3);
    }

    /* ===== Score Badge ===== */
    .score-badge {
        display: inline-block;
        background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
        color: #0e1117;
        padding: 4px 14px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.8rem;
    }

    /* ===== Category Tag ===== */
    .category-tag {
        display: inline-block;
        background: rgba(102, 126, 234, 0.15);
        color: #8b9cf7;
        padding: 4px 12px;
        border-radius: 10px;
        font-size: 0.75rem;
        font-weight: 600;
        margin-right: 6px;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }

    /* ===== Sidebar ===== */
    [data-testid="stSidebar"] {
        background: #12151e !important;
        border-right: 1px solid rgba(255,255,255,0.04);
    }
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] li,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span,
    [data-testid="stSidebar"] label {
        color: #9ca3af !important;
    }
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] h4,
    [data-testid="stSidebar"] h5 {
        color: #ffffff !important;
    }
    [data-testid="stSidebar"] strong {
        color: #c4b5fd !important;
    }
    [data-testid="stSidebar"] code {
        background: rgba(255,255,255,0.06) !important;
        color: #9ca3af !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 6px !important;
        padding: 4px 10px !important;
        font-size: 0.8rem !important;
    }

    /* ===== Inputs Dark Theme ===== */
    .stTextInput > div > div > input {
        background: #1a1f2e !important;
        border: 1px solid rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        color: #e0e0e0 !important;
        padding: 0.75rem 1rem !important;
        font-family: 'Inter', sans-serif !important;
    }
    .stTextInput > div > div > input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2) !important;
    }
    .stTextInput > div > div > input::placeholder {
        color: #4a4f62 !important;
    }

    /* ===== File Uploader Dark ===== */
    [data-testid="stFileUploader"] {
        background: #1a1f2e !important;
        border: 2px dashed rgba(255,255,255,0.08) !important;
        border-radius: 12px !important;
        padding: 1rem !important;
    }
    [data-testid="stFileUploader"]:hover {
        border-color: rgba(102, 126, 234, 0.3) !important;
    }
    [data-testid="stFileUploader"] section {
        background: transparent !important;
    }
    [data-testid="stFileUploader"] button {
        background: rgba(255,255,255,0.06) !important;
        color: #9ca3af !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 8px !important;
    }

    /* ===== Primary Button (Search) ===== */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"] {
        background: linear-gradient(135deg, #e74c6f 0%, #ff6b6b 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        letter-spacing: 0.3px;
        box-shadow: 0 4px 15px rgba(231, 76, 111, 0.3) !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover {
        box-shadow: 0 6px 25px rgba(231, 76, 111, 0.45) !important;
        transform: translateY(-1px);
    }

    /* ===== Secondary Buttons (Claim) ===== */
    .stButton > button[kind="secondary"],
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]) {
        background: rgba(102, 126, 234, 0.1) !important;
        color: #8b9cf7 !important;
        border: 1px solid rgba(102, 126, 234, 0.2) !important;
        border-radius: 10px !important;
        font-weight: 600 !important;
        transition: all 0.2s ease !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):hover {
        background: rgba(102, 126, 234, 0.2) !important;
        border-color: rgba(102, 126, 234, 0.4) !important;
    }

    /* ===== Progress Bar ===== */
    .stProgress > div > div > div {
        background: linear-gradient(90deg, #667eea, #764ba2) !important;
        border-radius: 10px !important;
    }
    .stProgress > div > div {
        background: rgba(255,255,255,0.06) !important;
        border-radius: 10px !important;
    }

    /* ===== Dividers ===== */
    hr {
        border-color: rgba(255,255,255,0.06) !important;
    }

    /* ===== Success/Info/Warning boxes ===== */
    .stAlert {
        border-radius: 10px !important;
    }
    [data-testid="stAlert"] {
        background: rgba(102, 126, 234, 0.08) !important;
        border: 1px solid rgba(102, 126, 234, 0.15) !important;
        border-radius: 10px !important;
    }

    /* ===== Spinner ===== */
    .stSpinner > div {
        color: #667eea !important;
    }

    /* ===== Hide Streamlit chrome ===== */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header[data-testid="stHeader"] {
        background: transparent !important;
    }

    /* ===== Image styling ===== */
    [data-testid="stImage"] img {
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.06);
    }

    /* ===== Labels ===== */
    .stTextInput label,
    .stFileUploader label {
        color: #9ca3af !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }

    /* ===== Expander ===== */
    .streamlit-expanderHeader {
        background: #1a1f2e !important;
        border-radius: 10px !important;
    }

    /* ===== RESPONSIVE ===== */
    @media (max-width: 992px) {
        .hero-banner {
            padding: 2rem 1.5rem;
        }
        .hero-banner h1 {
            font-size: 1.6rem;
        }
    }

    @media (max-width: 640px) {
        .hero-banner {
            padding: 1.5rem 1rem;
            border-radius: 14px;
            margin-bottom: 1rem;
        }
        .hero-banner h1 {
            font-size: 1.3rem;
        }
        .hero-banner p {
            font-size: 0.85rem;
        }
        .stat-number {
            font-size: 1.5rem;
        }
        .stat-label {
            font-size: 0.7rem;
        }
        .score-badge {
            font-size: 0.7rem;
            padding: 3px 10px;
        }
        .category-tag {
            font-size: 0.65rem;
            padding: 3px 8px;
        }
        [data-testid="stHorizontalBlock"] {
            flex-direction: column !important;
        }
        [data-testid="stHorizontalBlock"] > div {
            width: 100% !important;
            flex: 1 1 100% !important;
        }
    }

    @media (max-width: 400px) {
        .hero-banner h1 {
            font-size: 1.1rem;
        }
        .stat-number {
            font-size: 1.3rem;
        }
        .main .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.image("https://img.icons8.com/3d-fluency/94/search.png", width=55)
    st.title("About")
    st.markdown("""
    **Lost & Found Reunion** is a multi-modal
    semantic search engine built for BLDEACET campus.

    🧠 **How it works:**
    - Describe your lost item in plain English
    - Optionally upload a photo of a similar item
    - Our AI matches your query against the database
      using **semantic understanding** (not just keywords!)

    🔧 **Tech Stack:**
    - 🧬 Sentence-Transformers (MiniLM)
    - 👁️ CLIP (Vision + Language)
    - 🗄️ ChromaDB (Vector Store)
    - 🤖 Grok AI (Explanations)
    - 🖥️ Streamlit (UI)
    """)

    st.divider()
    st.markdown("##### 💡 Try these queries:")
    st.code("black noise cancelling headphones")
    st.code("red backpack with buckles")
    st.code("blue water bottle with straw")
    st.code("graphing calculator for math")
    st.code("small white wireless earbuds")
    st.code("cricket bat from sports room")
    st.code("brown leather wallet")

    st.divider()
    st.caption("Built with ❤️ for BLDEACET Lost & Found")

# ---------------------------------------------------------------------------
# Hero Banner
# ---------------------------------------------------------------------------
st.markdown("""
<div class="hero-banner">
    <h1><span class="hero-icon">🔍</span> Lost & Found Reunion — BLDEACET</h1>
    <p>Describe or upload a photo of your lost item — our AI will find the best matches</p>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Stats Row
# ---------------------------------------------------------------------------
try:
    import pandas as pd
    csv_path = os.path.join(BASE_DIR, "data", "lost_found_dataset_cleaned.csv")
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        s1, s2, s3 = st.columns(3)
        with s1:
            st.markdown(
                '<div class="stat-card">'
                '<div class="stat-icon">📋</div>'
                f'<div class="stat-number">{len(df)}</div>'
                '<div class="stat-label">Items in Database</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        with s2:
            st.markdown(
                '<div class="stat-card">'
                '<div class="stat-icon">📂</div>'
                f'<div class="stat-number">{df["category"].nunique()}</div>'
                '<div class="stat-label">Categories</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        with s3:
            st.markdown(
                '<div class="stat-card">'
                '<div class="stat-icon">🔢</div>'
                '<div class="stat-number">896</div>'
                '<div class="stat-label">Embedding Dimensions</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        st.markdown("")  # spacer
except Exception:
    pass

# ---------------------------------------------------------------------------
# Search Inputs
# ---------------------------------------------------------------------------
query_text = st.text_input(
    "📝 Describe your lost item...",
    placeholder="e.g., black noise cancelling headphones",
    help="Use natural language — the system understands synonyms!",
)

uploaded_file = st.file_uploader(
    "📷 Upload a photo (optional)",
    type=["jpg", "jpeg", "png", "webp"],
    help="Upload a photo of a similar item to improve results",
)

# Parse uploaded image
query_image = None
if uploaded_file:
    query_image = Image.open(uploaded_file)
    st.image(query_image, caption="Uploaded image", width=150)

# ---------------------------------------------------------------------------
# Search Button
# ---------------------------------------------------------------------------
search_clicked = st.button(
    "● Search Lost & Found",
    type="primary",
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# Results
# ---------------------------------------------------------------------------
if search_clicked:
    if not query_text and query_image is None:
        st.warning("⚠️ Please enter a text description or upload an image to search.")
    else:
        with st.spinner("🔍 Searching the Lost & Found database..."):
            try:
                results = search(
                    query_text=query_text if query_text else None,
                    query_image=query_image,
                    top_k=5,
                )
            except Exception as e:
                st.error(f"❌ Search error: {e}")
                st.info("Make sure you've run `python build_embeddings.py` first.")
                results = []

        if not results:
            st.info("😕 No matching items found. Try a different description or image.")
        else:
            st.markdown(f"### 🎯 Top {len(results)} Matches")
            st.divider()

            for i, item in enumerate(results):
                with st.container():
                    img_col, info_col = st.columns([1, 3])

                    with img_col:
                        img_path = os.path.join(BASE_DIR, item["image_path"]) if item.get("image_path") else ""
                        if img_path and os.path.exists(img_path):
                            st.image(img_path, use_container_width=True)
                        else:
                            st.image(
                                "https://placehold.co/300x300/1a1f2e/4a4f62?text=No+Image",
                                use_container_width=True,
                            )

                    with info_col:
                        # Name
                        st.markdown(f"#### {item['product_name']}")

                        # Category + Score badges
                        st.markdown(
                            f'<span class="category-tag">{item["category"]}</span>'
                            f'<span class="score-badge">{item["score"]:.1f}% match</span>',
                            unsafe_allow_html=True,
                        )

                        # Confidence bar
                        st.progress(min(item["score"] / 100.0, 1.0))

                        # AI Explanation
                        with st.spinner("Generating AI explanation..."):
                            explanation = get_ai_explanation(
                                query=query_text or "image search",
                                product_name=item["product_name"],
                                description=item.get("document", ""),
                            )
                        st.success(f"🤖 **AI Analysis:** {explanation}")

                        # Claim button
                        claim_key = f"claim_{i}_{item['product_id']}"
                        if st.button("✅ Claim This Item", key=claim_key):
                            st.balloons()
                            st.toast(
                                f"🎉 Claim submitted for '{item['product_name']}'! "
                                f"Visit the Lost & Found office to pick it up.",
                                icon="✅",
                            )

                    st.divider()

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    "<div style='text-align:center; opacity:0.35; font-size:0.8rem; color:#8b8fa3;'>"
    "Lost & Found Reunion v1.0 — BLDEACET Campus • "
    "Powered by Sentence-Transformers, CLIP, ChromaDB & Grok AI"
    "</div>",
    unsafe_allow_html=True,
)
