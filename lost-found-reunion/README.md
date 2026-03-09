# 🔍 Lost & Found Reunion — BLDEACET

A **multi-modal semantic search engine** for a college Lost & Found system.  
Students can search for lost items using **text descriptions** and/or **images**.  
The system semantically understands that *"wireless headphones"* ≈ *"AirPods"* ≈ *"earbuds"*.

> **1500+ items** across **17 categories** with real product images and AI-powered explanations.

---

## 📌 Problem Statement

Traditional lost & found systems rely on exact keyword matching, making it nearly
impossible for a student to find their "black Sony over-ear headphones" when the
item was logged as "WH-1000XM5 Wireless NC Headphones". This project bridges that
gap using **semantic embeddings** (sentence-transformers + CLIP) and a **vector
database** (ChromaDB) to return meaningful matches even when descriptions differ.

---

## 🏗️ Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    STREAMLIT UI (app.py)                  │
│  ┌─────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │ Text Input   │  │ Image Upload │  │ Results Cards  │  │
│  └──────┬───────┘  └──────┬───────┘  └───────▲────────┘  │
│         │                 │                  │            │
│         ▼                 ▼                  │            │
│  ┌─────────────────────────────────┐         │            │
│  │     search_engine.py            │         │            │
│  │  ┌───────────┐ ┌─────────────┐  │         │            │
│  │  │ MiniLM    │ │ CLIP        │  │         │            │
│  │  │ (384-d)   │ │ (512-d)     │  │         │            │
│  │  └─────┬─────┘ └──────┬──────┘  │         │            │
│  │        │               │         │         │            │
│  │        ▼               ▼         │         │            │
│  │  ┌─────────────────────────┐     │         │            │
│  │  │ Concatenate + Normalize │     │         │            │
│  │  │ (896-d combined vector) │     │         │            │
│  │  └───────────┬─────────────┘     │         │            │
│  │              │                   │         │            │
│  │              ▼                   │         │            │
│  │  ┌─────────────────────────┐     │         │            │
│  │  │ ChromaDB Cosine Search  │─────┼─────────┘            │
│  │  └─────────────────────────┘     │                      │
│  └─────────────────────────────────┘                      │
│                                                            │
│  ┌─────────────────────────────────┐                      │
│  │ Grok API (AI Explanations)      │                      │
│  └─────────────────────────────────┘                      │
└──────────────────────────────────────────────────────────┘

DATA PIPELINE (run once):
  create_sample_data.py ──▶ download_1000_products.py ──▶ clean_data.py ──▶ build_embeddings.py
         │                          │                          │                    │
         ▼                          ▼                          ▼                    ▼
  500 base products          1000 more products           cleaned.csv     ChromaDB + .pkl
  + picsum images            + DuckDuckGo images
```

---

## 📂 Folder Structure

```
lost-found-reunion/
├── app.py                        # Streamlit UI (dark theme, responsive)
├── scrape_data.py                # Phase 1a: live web scraping
├── create_sample_data.py         # Phase 1b: generate 500 base products
├── download_real_images.py       # Phase 1c: download real images (first 500)
├── download_1000_products.py     # Phase 1d: add 1000 more products (10 categories)
├── remove_duplicates.py          # Utility: remove duplicate images
├── clean_data.py                 # Phase 2: data cleaning
├── build_embeddings.py           # Phase 3: text + image embeddings
├── search_engine.py              # Core search + AI explanation logic
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml               # Dark theme configuration
├── data/
│   ├── scraped_products.csv       # Raw data (1500 products)
│   └── lost_found_dataset_cleaned.csv
├── embeddings/
│   └── lost_found_embeddings.pkl
├── images/
│   └── product_0001.jpg ...       # Real product images
└── chroma_db/                     # ChromaDB persistent vector store
```

---

## 📊 Dataset Overview

| Category | Items | Description |
|----------|-------|-------------|
| Electronics | 60 | Headphones, speakers, power banks, mice |
| Bags | 56 | Backpacks, duffel bags, sling bags |
| Clothing | 76 | Jackets, shoes, sunglasses, jeans |
| Books | 79 | Textbooks, novels, notebooks |
| Accessories | 73 | Water bottles, watches, wallets |
| Sports Equipment | 74 | Balls, rackets, fitness gear |
| Stationery | 82 | Pens, calculators, rulers |
| Smartphones | 100 | iPhone, Samsung, OnePlus, Xiaomi, POCO |
| Audio & Headphones | 100 | Sony, AirPods, boAt, JBL, Bose |
| Laptops | 100 | MacBook, Dell, HP, Lenovo, ASUS |
| Smartwatches | 100 | Apple Watch, Galaxy Watch, Noise, Fitbit |
| Cameras | 100 | Canon, Sony, GoPro, DJI, Nikon |
| Cricket & Badminton | 100 | SG bats, Yonex rackets, gloves, pads |
| Musical Instruments | 100 | Yamaha guitar, Casio keyboard, tabla |
| Gaming Accessories | 100 | PS5 controller, Logitech, Razer |
| Mobile Accessories | 100 | Power banks, chargers, cases, gimbals |
| Stationery & Calculators | 100 | Casio FX-991, Parker pens, Wacom |

**Total: 1500 products** with real product images and AI-generated lost-item descriptions.

---

## 🚀 Setup Instructions

### 1. Clone / navigate to the project directory

```bash
cd lost-found-reunion
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
pip install duckduckgo-search   # For image downloads
```

### 4. Set your xAI Grok API key

```bash
set XAI_API_KEY=your-api-key             # Windows (current session)
# export XAI_API_KEY=your-api-key        # macOS / Linux
```

Get a free key at [console.x.ai](https://console.x.ai/) (free $25/month credits)

### 5. Run the data pipeline (in order)

```bash
# Step 1: Generate base 500 products
python create_sample_data.py

# Step 2: Add 1000 more products with real images
python download_1000_products.py

# Step 3: Remove duplicate images
python remove_duplicates.py

# Step 4: Clean and build embeddings
python clean_data.py
python build_embeddings.py
```

### 6. Launch the app

```bash
python -m streamlit run app.py
```

The app will open at **http://localhost:8501** with the dark premium UI.

---

## 🔎 Sample Search Queries

| Query | Expected Top Match |
|-------|-------------------|
| "black noise cancelling headphones" | Audio / Sony WH-1000XM5 |
| "red backpack with zippers" | Bags / backpacks |
| "iPhone with titanium design" | Smartphones / iPhone 15 Pro |
| "cricket bat willow" | Cricket & Badminton / SG bat |
| "gaming mouse with RGB" | Gaming Accessories / Logitech |
| "blue water bottle with straw" | Accessories / Hydro Flask |
| "acoustic guitar yamaha" | Musical Instruments / Yamaha F310 |
| "graphing calculator for math" | Stationery / TI-84 Plus CE |
| Upload a photo of earbuds | Audio / AirPods, boAt |

---

## 🔧 Tech Stack

| Component | Technology |
|-----------|-----------|
| **UI** | Streamlit (dark glassmorphism theme) |
| **Text Embeddings** | Sentence-Transformers (all-MiniLM-L6-v2, 384-d) |
| **Image Embeddings** | CLIP (openai/clip-vit-base-patch32, 512-d) |
| **Vector Database** | ChromaDB (896-d combined vectors) |
| **AI Explanations** | xAI Grok API (grok-3-mini-fast) |
| **Image Source** | DuckDuckGo Image Search (no API key needed) |

---

## 🔮 Future Improvements

- **User accounts** — Let students register, submit lost items, and track claims.
- **Real-time notifications** — Alert students when a new item matches their lost-item profile.
- **GPS / location tagging** — Record where items were found on a campus map.
- **Fine-tuned CLIP** — Train on campus-specific items for higher accuracy.
- **Admin dashboard** — Manage inventory, verify claims, and generate reports.
- **Mobile app** — React Native or Flutter front-end for on-the-go searching.
- **Grok Vision** — Use Grok's multimodal capabilities for richer image understanding.

---

## 📄 License

This project is for educational purposes. Built for BLDEACET college.
