"""
Download 1000 product images with WHITE/PLAIN backgrounds from DuckDuckGo.
Amazon/Flipkart India style product photos only.

Appends to existing data (starts from product_501.jpg).
Keeps all previous images and data intact.

Usage:
    python download_1000_products.py
"""

import os
import csv
import time
import random
import hashlib
import requests
from PIL import Image
from tqdm import tqdm

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "images")
DATA_DIR = os.path.join(BASE_DIR, "data")
EXISTING_CSV = os.path.join(DATA_DIR, "scraped_products.csv")
OUTPUT_CSV = os.path.join(DATA_DIR, "scraped_products.csv")
IMAGE_SIZE = 300
START_ID = 501  # Continue from product_501.jpg

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0 Safari/537.36"
    )
}

# ---------------------------------------------------------------------------
# 10 Categories × 100 products each = 1000 products
# ---------------------------------------------------------------------------

CATEGORIES = {
    "Smartphones": {
        "queries": [
            "iPhone 15 pro product white background",
            "Samsung Galaxy S24 official product image",
            "OnePlus 12 product white background",
            "Realme smartphone product image flipkart",
            "Xiaomi Redmi Note product white background",
        ],
        "products": [
            ("iPhone 15 Pro Max 256GB", "6.7 inch Super Retina XDR display, A17 Pro chip, titanium design", 134900),
            ("iPhone 15 128GB", "6.1 inch display, A16 Bionic chip, Dynamic Island, 48MP camera", 79900),
            ("iPhone 14 128GB", "6.1 inch OLED display, A15 Bionic chip, dual camera system", 59900),
            ("Samsung Galaxy S24 Ultra", "6.8 inch QHD+ AMOLED, Snapdragon 8 Gen 3, S Pen, 200MP camera", 129999),
            ("Samsung Galaxy S24 Plus", "6.7 inch FHD+ AMOLED, Snapdragon 8 Gen 3, 50MP triple camera", 99999),
            ("Samsung Galaxy S23 FE", "6.4 inch FHD+ AMOLED, Exynos 2200, 50MP camera", 39999),
            ("Samsung Galaxy A55 5G", "6.6 inch Super AMOLED, Exynos 1480, 50MP triple camera", 29999),
            ("Samsung Galaxy M34 5G", "6.5 inch sAMOLED, Exynos 1280, 50MP triple camera, 6000mAh", 18999),
            ("OnePlus 12 256GB", "6.82 inch 2K LTPO AMOLED, Snapdragon 8 Gen 3, 50MP Hasselblad", 64999),
            ("OnePlus 12R 128GB", "6.78 inch LTPO AMOLED, Snapdragon 8 Gen 2, 50MP camera", 39999),
            ("OnePlus Nord CE4", "6.7 inch AMOLED, Snapdragon 7 Gen 3, 50MP camera, 100W charge", 24999),
            ("Realme GT 6T", "6.78 inch AMOLED, Snapdragon 7+ Gen 3, 50MP camera", 29999),
            ("Realme Narzo 70 Pro 5G", "6.7 inch AMOLED, Dimensity 7050, 50MP camera", 15999),
            ("Realme 12 Pro Plus", "6.7 inch curved AMOLED, Snapdragon 7s Gen 2, 64MP periscope", 23999),
            ("Xiaomi 14 256GB", "6.36 inch AMOLED, Snapdragon 8 Gen 3, Leica optics, 50MP", 69999),
            ("Redmi Note 13 Pro Plus", "6.67 inch AMOLED, Dimensity 7200, 200MP camera, 120W charge", 29999),
            ("Redmi Note 13 5G", "6.67 inch AMOLED, Dimensity 6080, 108MP camera", 17999),
            ("Redmi 13C", "6.74 inch HD+ display, Helio G85, 50MP camera, 5000mAh", 8999),
            ("POCO X6 Pro", "6.67 inch AMOLED, Dimensity 8300 Ultra, 64MP camera, 67W", 22999),
            ("POCO M6 5G", "6.74 inch HD+, Snapdragon 4 Gen 2, 50MP camera", 9499),
            ("Vivo V30 Pro", "6.78 inch AMOLED, Dimensity 8200, 50MP Zeiss camera", 39999),
            ("Vivo T3 5G", "6.67 inch AMOLED, Dimensity 7200, 50MP camera", 19999),
            ("iQOO Z9 5G", "6.67 inch AMOLED, Dimensity 7200, 50MP camera, 44W", 14999),
            ("Motorola Edge 50 Pro", "6.7 inch pOLED, Snapdragon 7 Gen 3, 50MP camera, 125W", 31999),
            ("Nothing Phone 2a", "6.7 inch AMOLED, Dimensity 7200, Glyph interface", 23999),
        ],
    },
    "Audio & Headphones": {
        "queries": [
            "Sony WH1000XM5 headphones white background",
            "AirPods Pro product white background",
            "boAt earphones product image",
            "JBL bluetooth speaker product white background",
            "boat rockerz headphones product image",
        ],
        "products": [
            ("Sony WH-1000XM5 Wireless Headphones", "Over-ear noise cancelling headphones, 30hr battery, LDAC", 29990),
            ("Sony WH-1000XM4 Headphones", "Over-ear ANC headphones, 30hr battery, multipoint", 19990),
            ("Sony WF-1000XM5 Earbuds", "True wireless ANC earbuds, LDAC, IPX4, 24hr total", 19990),
            ("Apple AirPods Pro 2nd Gen", "Active noise cancellation, MagSafe case, transparency mode", 24900),
            ("Apple AirPods 3rd Gen", "Spatial audio, sweat resistant, MagSafe charging case", 18900),
            ("Apple AirPods Max", "Over-ear headphones, ANC, Digital Crown, 20hr battery", 59900),
            ("Samsung Galaxy Buds2 Pro", "ANC earbuds, 360 Audio, IPX7, 29hr total battery", 17999),
            ("boAt Airdopes 141", "TWS earbuds, 42hr playback, IPX4, 8mm drivers", 1299),
            ("boAt Rockerz 450 Headphones", "On-ear wireless, 40mm drivers, 15hr battery, padded", 1499),
            ("boAt Rockerz 550 ANC", "Over-ear ANC headphones, 40mm drivers, 25hr battery", 2999),
            ("boAt BassHeads 100 Wired", "In-ear wired earphones, mic, HD sound, tangle-free", 399),
            ("boAt Stone 352 Speaker", "Portable Bluetooth speaker, 10W, IPX5, 12hr battery", 1299),
            ("JBL Flip 6 Speaker", "Portable Bluetooth, IP67 waterproof, 12hr, PartyBoost", 9999),
            ("JBL Charge 5 Speaker", "Portable Bluetooth, 20hr, power bank, IP67", 14999),
            ("JBL Tune 770NC Headphones", "Over-ear ANC, 44hr battery, multipoint, foldable", 5999),
            ("JBL Tune 230NC TWS", "ANC earbuds, 40hr total, IPX4, speed charge", 4999),
            ("JBL Go 3 Mini Speaker", "Ultra-portable, IP67, 5hr battery, compact design", 2999),
            ("Bose QuietComfort Ultra Earbuds", "Spatial audio, CustomTune ANC, 6hr battery", 24900),
            ("Bose SoundLink Flex Speaker", "Waterproof IP67, 12hr, PositionIQ, carabiner", 12900),
            ("Sennheiser HD 450BT Headphones", "Over-ear ANC, 30hr battery, aptX, foldable", 9990),
            ("OnePlus Buds 3 TWS", "ANC, LDAC, IP55, 44hr total, 12.4mm drivers", 5499),
            ("Noise Buds VS104 TWS", "TWS earbuds, 30hr total, Instacharge, Hyper Sync", 999),
            ("Sony SRS-XB100 Speaker", "Portable, IP67, 16hr battery, strap, compact", 3990),
            ("Marshall Emberton II Speaker", "Portable Bluetooth, 30hr, IP67, True Stereophonic", 14999),
            ("Jabra Elite 85t TWS", "ANC earbuds, 31hr total, semi-open design, IPX4", 12999),
        ],
    },
    "Laptops": {
        "queries": [
            "MacBook Air M2 product white background",
            "Dell XPS laptop product image",
            "HP laptop product white background",
            "Lenovo ThinkPad product image",
            "ASUS ROG laptop product white background",
        ],
        "products": [
            ("MacBook Air M2 256GB", "13.6 inch Liquid Retina, M2 chip, 8GB RAM, 18hr battery", 99900),
            ("MacBook Air M3 512GB", "15.3 inch Liquid Retina, M3 chip, 16GB RAM, 18hr battery", 139900),
            ("MacBook Pro 14 M3 Pro", "14 inch XDR, M3 Pro chip, 18GB RAM, 17hr battery", 199900),
            ("Dell XPS 13 Plus", "13.4 inch FHD+, Intel i7-1360P, 16GB, 512GB SSD", 129990),
            ("Dell Inspiron 15 3530", "15.6 inch FHD, Intel i5-1335U, 8GB, 512GB SSD", 54990),
            ("Dell G15 Gaming Laptop", "15.6 inch FHD 120Hz, i5-12500H, RTX 3050, 16GB", 69990),
            ("HP Pavilion 15", "15.6 inch FHD IPS, Intel i5-1335U, 16GB, 512GB SSD", 57990),
            ("HP Victus 16 Gaming", "16.1 inch FHD 144Hz, i5-12450H, RTX 4050, 16GB", 74990),
            ("HP Spectre x360 14", "13.5 inch 3K2K OLED, i7-1355U, 16GB, 1TB SSD", 139990),
            ("Lenovo ThinkPad E14 Gen 5", "14 inch FHD IPS, i5-1335U, 16GB, 512GB SSD", 62990),
            ("Lenovo IdeaPad Slim 3", "15.6 inch FHD, i3-1315U, 8GB, 256GB SSD", 35990),
            ("Lenovo Legion 5 Pro", "16 inch WQXGA 165Hz, R7-7745HX, RTX 4060, 16GB", 129990),
            ("ASUS ROG Strix G16", "16 inch FHD 165Hz, i7-13650HX, RTX 4060, 16GB", 109990),
            ("ASUS VivoBook 15", "15.6 inch FHD, i5-1235U, 8GB, 512GB SSD, thin", 47990),
            ("ASUS TUF Gaming A15", "15.6 inch FHD 144Hz, R7-7735HS, RTX 4050, 16GB", 89990),
            ("Acer Aspire 5 A515", "15.6 inch FHD IPS, i5-1335U, 16GB, 512GB SSD", 49990),
            ("Acer Nitro V Gaming", "15.6 inch FHD 144Hz, i5-13420H, RTX 4050, 16GB", 69990),
            ("Acer Swift Go 14", "14 inch 2.8K OLED, i7-1355U, 16GB, 512GB SSD", 89990),
            ("MSI GF63 Thin", "15.6 inch FHD, i5-12450H, RTX 2050, 8GB, 512GB", 49990),
            ("Samsung Galaxy Book3", "15.6 inch FHD AMOLED, i5-1335U, 8GB, 512GB SSD", 54990),
            ("Xiaomi Notebook Pro 120G", "14 inch 2.8K display, i5-12450H, 16GB, 512GB SSD", 44999),
            ("Realme Book Enhanced", "14 inch 2K IPS, i5-1135G7, 8GB, 512GB SSD", 39999),
            ("Microsoft Surface Laptop Go 3", "12.4 inch touchscreen, i5-1235U, 8GB, 256GB SSD", 79999),
            ("LG Gram 16", "16 inch WQXGA, i7-1360P, 16GB, 512GB SSD, ultra-light", 119990),
            ("Lenovo Yoga 7i 2-in-1", "14 inch 2.8K OLED, i7-1355U, 16GB, 512GB, touchscreen", 99990),
        ],
    },
    "Smartwatches": {
        "queries": [
            "Apple Watch Series 9 product white background",
            "Samsung Galaxy Watch product image",
            "Noise ColorFit smartwatch product",
            "boAt smartwatch product white background",
            "Fitbit smartwatch product image",
        ],
        "products": [
            ("Apple Watch Series 9 45mm", "Always-on Retina, S9 chip, blood oxygen, ECG, IP6X", 44900),
            ("Apple Watch SE 2nd Gen", "OLED display, S8 chip, crash detection, swim-proof", 29900),
            ("Apple Watch Ultra 2", "49mm titanium, dual frequency GPS, 36hr battery", 89900),
            ("Samsung Galaxy Watch6 Classic", "1.47 inch sAMOLED, rotating bezel, BioActive sensor", 34999),
            ("Samsung Galaxy Watch6 44mm", "1.47 inch sAMOLED, Exynos W930, BIA, sleep coaching", 26999),
            ("Samsung Galaxy Fit3", "1.6 inch AMOLED, swim-ready, 13 day battery, lightweight", 3999),
            ("Noise ColorFit Pulse 4", "1.85 inch display, BT calling, SpO2, 150+ watch faces", 1999),
            ("Noise ColorFit Pro 5", "1.85 inch AMOLED, BT calling, smart gesture, 7 day battery", 3999),
            ("Noise ColorFit Ultra 3", "1.96 inch AMOLED, stainless steel, BT calling, GPS", 4999),
            ("boAt Wave Sigma", "2.01 inch HD display, BT calling, SpO2, IP68", 1299),
            ("boAt Ultima Call Smartwatch", "1.83 inch AMOLED, BT calling, 700+ active modes", 1999),
            ("boAt Wave Lite Smartwatch", "1.69 inch HD display, SpO2, HR monitor, 10 day battery", 999),
            ("Fitbit Versa 4", "1.58 inch AMOLED, built-in GPS, 6+ day battery, Alexa", 14999),
            ("Fitbit Charge 6", "Health tracker, built-in GPS, 7 day battery, Google apps", 11999),
            ("Fitbit Inspire 3", "Color AMOLED, stress management, sleep tracking, 10 day", 7999),
            ("Amazfit GTR 4", "1.43 inch AMOLED, dual-band GPS, 14 day battery, Alexa", 14999),
            ("Amazfit Bip 5", "1.91 inch display, GPS, 10 day battery, 120+ sports modes", 5999),
            ("Fire-Boltt Phoenix Ultra", "1.28 inch AMOLED, BT calling, rotating crown, 7 day", 1499),
            ("Fire-Boltt Dream", "1.78 inch AMOLED, BT calling, always-on display, IP68", 1999),
            ("Garmin Venu Sq 2", "1.41 inch AMOLED, built-in GPS, 11 day battery, health", 24990),
            ("OnePlus Watch 2", "1.43 inch AMOLED, Snapdragon W5, 100hr battery, LTPO", 24999),
            ("Realme Watch S2", "1.43 inch AMOLED, BT calling, GPS, 20 day battery", 4999),
            ("Titan Smart Pro", "1.96 inch AMOLED, BT calling, SingleSync, 5 day battery", 6999),
            ("Fastrack Revoltt FS1", "1.83 inch display, BT calling, AI voice assistant, IP68", 1795),
            ("Xiaomi Watch S3", "1.43 inch AMOLED, GPS, SpO2, 15 day battery, rotating bezel", 8999),
        ],
    },
    "Cameras": {
        "queries": [
            "Canon DSLR camera product white background",
            "Sony mirrorless camera product image",
            "GoPro Hero product white background",
            "Nikon DSLR product image",
            "DJI Mini drone product white background",
        ],
        "products": [
            ("Canon EOS R50 Mirrorless", "24.2MP APS-C, 4K video, DIGIC X, Eye AF, compact body", 72990),
            ("Canon EOS 200D II DSLR Kit", "24.1MP, 4K video, Dual Pixel AF, vari-angle LCD", 54990),
            ("Canon EOS 1500D DSLR Kit", "24.1MP, Full HD, 9-point AF, Wi-Fi, beginner DSLR", 34990),
            ("Canon EOS M50 Mark II", "24.1MP, 4K video, Eye AF, vlogger-friendly, flip screen", 58990),
            ("Canon PowerShot G7 X Mark III", "20.1MP, 4K, 1-inch sensor, vlogging, live streaming", 52995),
            ("Sony Alpha A6400 Mirrorless", "24.2MP APS-C, 4K, real-time Eye AF, 11fps burst", 74990),
            ("Sony Alpha A7 III Full Frame", "24.2MP full frame, 4K HDR, 693 AF points, 5-axis IS", 149990),
            ("Sony ZV-1 Vlogging Camera", "20.1MP, 4K, background defocus, directional mic", 47990),
            ("Sony Alpha A6100 Kit", "24.2MP, 4K, 425 AF points, Eye AF, flip LCD", 54990),
            ("Nikon D3500 DSLR Kit", "24.2MP DX, Full HD, 11-point AF, Guide Mode, 1550 shots", 34990),
            ("Nikon Z50 Mirrorless Kit", "20.9MP DX, 4K, 209 AF points, flip LCD, compact", 72990),
            ("Nikon D5600 DSLR Kit", "24.2MP, Full HD, 39-point AF, touchscreen, Wi-Fi", 49990),
            ("Nikon Z30 Vlogging Kit", "20.9MP, 4K, Eye AF, no viewfinder, vari-angle LCD", 59990),
            ("GoPro Hero 12 Black", "5.3K60 video, HyperSmooth 6.0, waterproof 10m, HDR", 39990),
            ("GoPro Hero 11 Black Mini", "5.3K, HyperSmooth 5.0, compact, waterproof, rugged", 29990),
            ("DJI Mini 4 Pro Drone", "4K/60fps, 48MP, OcuSync 4, 34min flight, 249g", 84990),
            ("DJI Air 3 Drone", "Dual camera, 4K/100fps, 46min flight, omnidirectional sensing", 99990),
            ("DJI Osmo Action 4", "4K/120fps, 1/1.3 inch sensor, waterproof 18m, magnetic", 26990),
            ("Fujifilm Instax Mini 12", "Instant camera, auto exposure, selfie mirror, compact", 6599),
            ("Fujifilm X-T30 II Mirrorless", "26.1MP, 4K, film simulation, compact retro design", 89999),
            ("Panasonic Lumix G7 4K", "16MP, 4K photo/video, OLED viewfinder, touchscreen", 37990),
            ("DJI Pocket 3", "1-inch CMOS, 4K/120fps, 3-axis gimbal, rotatable screen", 39990),
            ("Insta360 X3", "5.7K 360 camera, FlowState, waterproof 10m, touchscreen", 37999),
            ("Canon EOS R6 Mark II", "24.2MP full frame, 4K 60p, 40fps burst, IBIS", 189990),
            ("Sony Alpha A7C Mirrorless", "24.2MP full frame, 4K, compact body, 5-axis IBIS", 139990),
        ],
    },
    "Cricket & Badminton Sports": {
        "queries": [
            "SG cricket bat product white background",
            "Yonex badminton racket product image",
            "SS cricket bat product white background",
            "cricket gloves SG product image",
            "batting pads cricket product white background",
            "cricket helmet product image",
            "badminton shuttlecock product white background",
        ],
        "products": [
            ("SG RSD Spark Kashmir Willow Bat", "Kashmir willow, full size, rubber grip, cane handle", 1299),
            ("SG Nexus Plus Kashmir Willow Bat", "Kashmir willow, thick edges, sarawak cane handle", 1899),
            ("SG Sierra 250 English Willow Bat", "English willow, Grade 2, mid-sweet spot, full size", 5999),
            ("SS Ton Slasher Kashmir Willow Bat", "Kashmir willow, lightweight, full size, SS branding", 1599),
            ("SS Gladiator English Willow Bat", "English willow, Grade 1, big edges, premium grip", 8999),
            ("MRF Genius Grand Edition Bat", "English willow, Virat Kohli edition, premium grade", 12999),
            ("Kookaburra Kahuna 5.0 Bat", "English willow, sweet spot, lightweight pickup", 7999),
            ("SG Test Pro Batting Gloves", "Leather palm, high density foam, flexible fingers", 1499),
            ("SS Platino Batting Gloves", "Pittards leather, finger rolls, ventilation mesh", 1999),
            ("SG Club Batting Pads", "Lightweight pads, three straps, PVC facing, full size", 1299),
            ("SS Test Opener Batting Pads", "Traditional shape, bolted knee roll, cane rods", 2499),
            ("SG Aeroguard Cricket Helmet", "Steel grille, high impact shell, adjustable fit", 2499),
            ("Masuri VS Test Titanium Helmet", "Titanium grille, stem guard, ventilation, premium", 8999),
            ("SG Test White Cricket Ball", "4-piece leather, hand stitched, alum tanned, match", 699),
            ("Kookaburra Turf Red Cricket Ball", "4-piece, machine stitched, grade A leather", 899),
            ("Yonex Nanoray 10F Badminton Racket", "Isometric head, lightweight 3U, carbon shaft", 2490),
            ("Yonex Astrox 88S Pro Racket", "Rotational generator, stiff flex, 4U, head heavy", 15990),
            ("Yonex Mavis 350 Shuttlecock Pack", "Nylon shuttle, medium speed, tournament grade, 6 pcs", 599),
            ("Li-Ning Smash XP 90 IV Racket", "Isometric frame, steel shaft, full cover included", 899),
            ("Li-Ning Windstorm 78 Racket", "Ultra-light 5U, carbon fiber, flexible shaft", 3499),
            ("Victor Thruster K Onigiri Racket", "Carbon fiber, head heavy, stiff shaft, power play", 5999),
            ("Cosco CBX 320 Badminton Racket", "Aluminium frame, steel shaft, beginner level", 399),
            ("SG Campus Cricket Kit Bag", "Full kit bag, multiple compartments, shoe pocket", 2499),
            ("SS Sunridges Cricket Kit Bag", "Wheelie bag, bat pocket, shoe compartment, large", 3999),
            ("SG Inner Batting Gloves", "Cotton padded, full finger, sweat absorption", 299),
        ],
    },
    "Musical Instruments": {
        "queries": [
            "Yamaha acoustic guitar product white background",
            "Casio keyboard piano product image",
            "tabla musical instrument product white background",
            "harmonium instrument product image",
            "violin instrument product white background",
            "ukulele product white background",
            "cajon drum product image",
        ],
        "products": [
            ("Yamaha F310 Acoustic Guitar", "Dreadnought, spruce top, meranti back/sides, full size", 9990),
            ("Yamaha C40 Classical Guitar", "Nylon string, spruce top, 39 inch, beginner", 7990),
            ("Yamaha FG800 Acoustic Guitar", "Solid spruce top, nato back/sides, scalloped bracing", 13990),
            ("Fender CD-60S Dreadnought Guitar", "Solid mahogany top, rolled fingerboard, natural", 14990),
            ("Ibanez V50NJP Acoustic Guitar Pack", "Spruce top, agathis, gig bag and accessories", 7999),
            ("Kadence Frontier Acoustic Guitar", "Spruce top, rosewood fingerboard, 41 inch, cutaway", 3999),
            ("Casio CT-S200 Portable Keyboard", "61 keys, 400 tones, Dance Music Mode, battery/adapter", 7995),
            ("Casio CT-X700 Keyboard", "61 keys, 600 tones, AiX Sound Source, USB MIDI", 11995),
            ("Casio SA-78 Mini Keyboard", "44 keys, 100 tones, compact, battery powered, kids", 3395),
            ("Yamaha PSR-E373 Keyboard", "61 keys, touch response, 622 voices, USB to host", 13490),
            ("Yamaha PSR-I500 Indian Keyboard", "61 keys, tabla/tanpura, raga guide, Indian tones", 17990),
            ("Roland FP-30X Digital Piano", "88 keys, PHA-4 hammer action, Bluetooth, twin speakers", 64990),
            ("Kadence KAD-TAB Tabla Set", "Dayan + Bayan, sheesham wood, goat skin, with cover", 4999),
            ("SG Musical Tabla Set Premium", "Professional tabla pair, brass bayan, tuning hammer", 7999),
            ("Monoj Kumar Sardar Harmonium", "3.25 octave, 9 stopper, coupler, double reed, bellows", 12999),
            ("Paloma Harmonium 7 Stopper", "3 octave, 7 stopper, bass-male, teak wood body", 7999),
            ("Stentor Student I Violin 4/4", "Solid spruce top, maple back/sides, ebony fittings", 8990),
            ("Kadence KAD-VIO Violin Set", "4/4 full size, spruce top, bow and case included", 3499),
            ("Kadence KAD-UKE Soprano Ukulele", "21 inch, sapele wood, nylon strings, open gear tuners", 1499),
            ("Yamaha GL1 Guitalele", "6 nylon strings, compact 17 inch, spruce top, meranti", 5990),
            ("Meinl HCAJ1NT Headliner Cajon", "Baltic birch body, adjustable snare, natural finish", 7499),
            ("Kadence CL350 Cajon", "Birch body, internal snare wire, padded bag included", 3499),
            ("Yamaha YRS-24B Soprano Recorder", "ABS resin, 3-piece, baroque fingering, school use", 490),
            ("Rajasthani Dholak Sheesham Wood", "Rope-tuned, mango/sheesham wood, goat skin heads", 2499),
            ("Yamaha YFL-222 Flute", "Silver-plated, C key, offset G, split E, student", 27990),
        ],
    },
    "Gaming Accessories": {
        "queries": [
            "PS5 DualSense controller product white background",
            "Xbox controller product white background",
            "Logitech gaming mouse product image",
            "mechanical keyboard gaming product white background",
            "gaming headset product white background",
        ],
        "products": [
            ("Sony DualSense PS5 Controller White", "Haptic feedback, adaptive triggers, built-in mic", 5990),
            ("Sony DualSense PS5 Controller Black", "Haptic feedback, adaptive triggers, USB-C, black", 5990),
            ("Sony PS5 DualSense Edge Controller", "Pro controller, customizable, back buttons, OLED", 18990),
            ("Xbox Wireless Controller Carbon Black", "Textured grip, Bluetooth, 3.5mm jack, USB-C", 5590),
            ("Xbox Wireless Controller Robot White", "Ergonomic, hybrid D-pad, share button, USB-C", 5590),
            ("Xbox Elite Series 2 Controller", "Pro controller, adjustable tension, 40hr battery", 14990),
            ("Logitech G502 X Gaming Mouse", "25K HERO sensor, LIGHTFORCE switches, DPI shift", 5495),
            ("Logitech G Pro X Superlight", "25K HERO sensor, 63g ultra-light, PTFE feet", 9995),
            ("Logitech G203 Lightsync Mouse", "8000 DPI, 6 buttons, RGB, lightweight gaming", 1795),
            ("Razer DeathAdder V3", "30K sensor, 90hr battery, HyperSpeed wireless, 63g", 12999),
            ("Razer Viper V2 Pro", "30K sensor, 58g, HyperSpeed, optical switches", 14999),
            ("SteelSeries Rival 3 Mouse", "TrueMove Core sensor, RGB, 6 buttons, lightweight", 2699),
            ("Cosmic Byte CB-GK-21 Mechanical KB", "Outemu Blue switches, RGB, full size, USB", 2299),
            ("HyperX Alloy Origins 60 Keyboard", "60% compact, HyperX Red switches, RGB, aluminum", 7999),
            ("Razer BlackWidow V4 Keyboard", "Green switches, full size, RGB, magnetic wrist rest", 14999),
            ("Logitech G213 Prodigy Keyboard", "Membrane gaming, RGB zones, palmrest, spill-resistant", 3295),
            ("Ant Esports MK1200 Mini Keyboard", "60% compact, Outemu Blue, RGB, detachable cable", 1799),
            ("HyperX Cloud II Gaming Headset", "7.1 surround, 53mm drivers, detachable mic, comfort", 5999),
            ("Razer Kraken V3 X Headset", "7.1 surround, TriForce 40mm, HyperClear mic, USB", 3999),
            ("SteelSeries Arctis 7+ Headset", "Wireless, 30hr battery, ClearCast mic, comfort band", 12999),
            ("Logitech G435 Wireless Headset", "Lightspeed/BT, 18hr battery, 165g, dual beamform mic", 5995),
            ("Cosmic Byte GS430 Gaming Headset", "7.1 surround, RGB, detachable mic, USB, over-ear", 999),
            ("Razer Goliathus Extended Mouse Pad", "XXL size, micro-textured, anti-slip rubber base", 2999),
            ("SteelSeries QcK Heavy Gaming Pad", "Extra thick, micro-woven, non-slip rubber, XL", 2499),
            ("Razer Kiyo Pro Webcam", "1080p/60fps, adaptive light sensor, HDR, USB 3.0", 9999),
        ],
    },
    "Mobile Accessories": {
        "queries": [
            "power bank 20000mah product white background",
            "USB C charger product image",
            "phone case transparent product",
            "selfie stick product white background",
            "wireless charger product image",
        ],
        "products": [
            ("Mi Power Bank 3i 20000mAh", "20000mAh, dual USB output, 18W fast charge, slim", 1599),
            ("Anker PowerCore 20000mAh", "Dual USB, PowerIQ, 20000mAh, portable, fast charge", 3499),
            ("Samsung 10000mAh Power Bank", "25W fast charge, USB-C, sleek design, compact", 2199),
            ("Ambrane 27000mAh Power Bank", "65W PD, laptop charging, triple port, LED display", 3999),
            ("Realme 20000mAh Power Bank", "18W two-way fast charge, dual USB, slim design", 1499),
            ("Apple 20W USB-C Charger", "20W fast charging, USB-C, compact, for iPhone/iPad", 1900),
            ("Samsung 25W USB-C Charger", "25W super fast, USB-C, PPS, compact adapter", 1099),
            ("OnePlus SUPERVOOC 80W Charger", "80W Warp Charge, USB-A, compatible with OnePlus", 1999),
            ("Anker Nano 3 30W GaN Charger", "30W, USB-C, GaN II, foldable plug, ultra-compact", 1799),
            ("Belkin BoostCharge 65W GaN", "65W, dual USB-C, GaN tech, laptop + phone charging", 3999),
            ("Apple MagSafe Charger", "15W wireless, magnetic alignment, for iPhone 12+", 4500),
            ("Samsung 15W Wireless Charger Pad", "15W Qi charging, LED indicator, USB-C, slim", 2199),
            ("Belkin 10W Wireless Charging Stand", "10W Qi, upright stand, LED indicator, USB-C", 2999),
            ("boAt Instacharge 1 Wireless Pad", "10W Qi wireless, anti-slip, LED, compact design", 799),
            ("Spigen Ultra Hybrid iPhone 15 Case", "Clear TPU bumper, polycarbonate back, mil-grade", 1299),
            ("Ringke Fusion Galaxy S24 Case", "Clear back, TPU frame, lanyard hole, anti-yellow", 999),
            ("ESR Armorite iPhone 15 Pro Case", "MagSafe, military grade, clear, yellowing resistant", 1799),
            ("Portronics Lumistick Selfie Stick", "Extendable, Bluetooth remote, tripod, 360 rotation", 699),
            ("Mi Selfie Stick Tripod", "Bluetooth remote, extendable, tripod stand, compact", 999),
            ("DJI OM 6 Smartphone Gimbal", "3-axis stabilizer, ActiveTrack 5.0, gesture control", 12990),
            ("boAt USB-C to Lightning Cable", "MFi certified, 1m, fast charge, braided nylon", 699),
            ("Anker USB-C to USB-C Cable 2m", "100W PD, braided, USB 2.0, for laptop/phone", 999),
            ("Spigen OneTap MagSafe Car Mount", "Magnetic, air vent mount, 360 rotation, one hand", 1999),
            ("iOtus MagSafe Car Charger Mount", "15W wireless, magnetic, air vent, fast charge", 2499),
            ("Ambrane Earphone Jack Splitter", "3.5mm audio splitter, dual port, TPE cable, compact", 199),
        ],
    },
    "Stationery & Calculators": {
        "queries": [
            "Casio fx-991 calculator product white background",
            "geometry box product image",
            "Parker fountain pen product white background",
            "Wacom drawing tablet product image",
            "stapler product white background",
        ],
        "products": [
            ("Casio FX-991EX Scientific Calculator", "552 functions, spreadsheet, natural display, solar+battery", 1595),
            ("Casio FX-82MS 2nd Gen Calculator", "240 functions, 2-line display, scientific, battery", 595),
            ("Casio FX-991CW Calculator", "Over 290 functions, high-res LCD, ClassWiz, QR code", 1995),
            ("Texas Instruments TI-84 Plus CE", "Color graphing calculator, rechargeable, MathPrint", 12999),
            ("Oreva Scientific Calculator", "240 functions, 2-line display, budget scientific", 349),
            ("Parker Vector Standard Fountain Pen", "Stainless steel nib, matte black, ink cartridge", 295),
            ("Parker Jotter Ballpoint Pen", "Stainless steel, quink refill, classic design, gift box", 495),
            ("Parker IM Premium Fountain Pen", "Gold trim, lacquer finish, premium nib, gift box", 2495),
            ("Pilot V7 Hi-Tecpoint Pen Pack of 3", "0.7mm fine tip, liquid ink, smooth writing", 270),
            ("Lamy Safari Fountain Pen", "ABS body, steel nib, ergonomic grip, cartridge/converter", 2990),
            ("Faber-Castell Geometry Box", "Metal box, compass, protractor, divider, set squares", 395),
            ("Camlin Kokuyo Geometry Box", "Plastic box, compass, protractor, scale, set squares", 185),
            ("Staedtler Geometry Set", "Metal compass, ruler, set squares, protractor, premium", 599),
            ("Wacom Intuos S Drawing Tablet", "4x3 inch, 4096 pressure levels, USB, Bluetooth", 5499),
            ("Wacom One 13 Pen Display", "13.3 inch FHD, pen display, 4096 levels, color accurate", 28990),
            ("XP-Pen Deco 01 V2 Tablet", "10x6.25 inch, 8192 levels, tilt support, USB-C", 3999),
            ("Kangaro DP-480 Punch Machine", "Two-hole punch, 12 sheet capacity, metal, adjustable", 225),
            ("Kangaro HD-10D Stapler", "No.10 stapler, 20 sheet capacity, metal body, compact", 120),
            ("Swingline Heavy Duty Stapler", "160 sheet capacity, reduced effort, metal, office", 2499),
            ("Post-it Super Sticky Notes 3x3", "90 sheets, 5 pads, bright neon colors, repositionable", 449),
            ("Classmate Pulse 6-Subject Notebook", "300 pages, single line, spiral binding, soft cover", 210),
            ("Five Star 5-Subject Notebook", "200 pages, college ruled, divider tabs, spiral", 549),
            ("Zebra Sarasa Clip Gel Pen Set 10", "0.5mm, retractable, rubber grip, assorted colors", 750),
            ("Faber-Castell Colour Pencils 48 Set", "48 shades, break-resistant, tin box, sharpener", 899),
            ("Doms Sketch Set 50 Piece", "Color pencils, sketch pens, crayons, sharpener, eraser", 399),
        ],
    },
}

# ---------------------------------------------------------------------------
# Lost item description templates
# ---------------------------------------------------------------------------
LOCATIONS = [
    "near the library", "in the cafeteria", "at the bus stop", "in the lecture hall",
    "near the gym", "in the computer lab", "in the student center", "near the parking lot",
    "in the auditorium", "at the sports complex", "in the hostel lobby", "in the laundry room",
    "near the dormitory", "in the common room", "at the canteen", "near the main gate",
    "in the seminar hall", "at the basketball court", "in the reading room", "near the ATM",
    "in the washroom", "by the vending machine", "at the food court", "in the garden area",
    "in the drawing hall", "at the workshop", "in the music room", "near the admin block",
]

LOST_TEMPLATES = [
    "I lost my {item} somewhere {loc}, it's {detail}",
    "Can't find my {item}, I last had it {loc}, it's {detail}",
    "My {item} went missing {loc}, {detail}",
    "Left my {item} {loc} and can't find it now, {detail}",
    "Has anyone seen my {item}? I lost it {loc}, {detail}",
    "Missing my {item} since yesterday, probably {loc}, {detail}",
    "I think I dropped my {item} {loc}, {detail}",
]

DETAILS = [
    "kinda scratched but works fine", "pretty new bought last month",
    "has a small sticker on it", "a bit worn out", "has my name tag on it",
    "slightly dusty but good condition", "the one I use for college daily",
    "I got it as a birthday gift", "common looking but it's mine",
    "medium size nothing fancy", "standard one everyone uses",
    "has a crack on the corner", "still in good shape though",
]

COLORS = [
    "Black", "White", "Grey", "Silver", "Blue", "Red", "Green",
    "Gold", "Rose Gold", "Space Grey", "Navy", "Purple", "Teal",
]


# ---------------------------------------------------------------------------
# Download image from DuckDuckGo
# ---------------------------------------------------------------------------
def search_and_download(product_id: int, query: str) -> str:
    """Search DuckDuckGo for product image and download it."""
    filename = f"product_{product_id:04d}.jpg"
    filepath = os.path.join(IMAGES_DIR, filename)

    if os.path.exists(filepath) and os.path.getsize(filepath) > 1000:
        return os.path.join("images", filename)

    try:
        from duckduckgo_search import DDGS

        with DDGS() as ddgs:
            results = list(ddgs.images(
                keywords=query,
                max_results=8,
                size="Medium",
                type_image="photo",
                layout="Square",
            ))

        if not results:
            return ""

        for result in results[:8]:
            img_url = result.get("image", "")
            if not img_url:
                continue
            try:
                resp = requests.get(img_url, headers=HEADERS, timeout=15, stream=True)
                resp.raise_for_status()
                ct = resp.headers.get("content-type", "")
                if "image" not in ct:
                    continue

                with open(filepath, "wb") as f:
                    for chunk in resp.iter_content(8192):
                        f.write(chunk)

                img = Image.open(filepath).convert("RGB")
                img = img.resize((IMAGE_SIZE, IMAGE_SIZE), Image.LANCZOS)
                img.save(filepath, "JPEG", quality=85)
                return os.path.join("images", filename)
            except Exception:
                continue
    except Exception:
        pass

    return ""


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("=" * 60)
    print("  Download 1000 Product Images (White Background)")
    print("  Using DuckDuckGo — No API Key Needed")
    print("=" * 60)

    os.makedirs(IMAGES_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)

    random.seed(123)

    # Load existing data
    existing_rows = []
    if os.path.exists(EXISTING_CSV):
        with open(EXISTING_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            existing_rows = list(reader)
        print(f"\n[Info] Loaded {len(existing_rows)} existing products (keeping them)")

    # Generate new products
    new_rows = []
    product_id = START_ID
    total_categories = len(CATEGORIES)

    for cat_idx, (cat_name, cat_data) in enumerate(CATEGORIES.items(), 1):
        products = cat_data["products"]
        queries = cat_data["queries"]
        items_per_cat = 100
        products_available = len(products)

        print(f"\n[{cat_idx}/{total_categories}] Category: {cat_name} ({items_per_cat} items)")

        # Generate `items_per_cat` items from base products + variations
        cat_items = []
        variation_suffixes = [
            "", " (Like New)", " (Renewed)", " (Bundle)", " (Limited Edition)",
            " (Campus Deal)", " (Student Special)", " (Open Box)", " (Gift Set)",
        ]

        idx = 0
        while len(cat_items) < items_per_cat:
            base_idx = idx % products_available
            name, desc, price = products[base_idx]

            # Add variation suffix for items beyond base count
            if idx >= products_available:
                suffix = variation_suffixes[(idx // products_available) % len(variation_suffixes)]
                name = name + suffix
            if name in [r["product_name"] for r in cat_items]:
                idx += 1
                continue

            color = random.choice(COLORS)
            loc = random.choice(LOCATIONS)
            detail = random.choice(DETAILS)
            template = random.choice(LOST_TEMPLATES)

            # Create a vague short name for lost description
            words = name.split("(")[0].split()
            vague_item = " ".join(words[-2:]) if len(words) > 2 else name

            lost_desc = template.format(item=vague_item, loc=loc, detail=detail)

            cat_items.append({
                "product_id": str(product_id),
                "product_name": name,
                "category": cat_name,
                "description": f"{color} {desc}",
                "price": f"{price:.2f}" if isinstance(price, float) else str(price),
                "image_url": "",
                "image_path": "",
                "lost_item_description": lost_desc,
            })
            product_id += 1
            idx += 1

        new_rows.extend(cat_items)

    print(f"\n[Info] Generated {len(new_rows)} new products across {total_categories} categories")

    # Download images
    print(f"\n[Downloading] Images from DuckDuckGo...")
    success = 0
    for row in tqdm(new_rows, desc="Downloading product images"):
        pid = int(row["product_id"])
        name = row["product_name"]
        cat_data_for_row = CATEGORIES.get(row["category"], {})
        queries = cat_data_for_row.get("queries", [])

        # Pick a query based on index
        query = random.choice(queries) if queries else f"{name} product white background"

        path = search_and_download(pid, query)
        row["image_path"] = path
        if path:
            success += 1

        time.sleep(0.3)  # Rate limit

    # Combine existing + new
    all_rows = existing_rows + new_rows

    # Save combined CSV
    fieldnames = [
        "product_id", "product_name", "category", "description",
        "price", "image_url", "image_path", "lost_item_description",
    ]
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_rows)

    # Summary
    print(f"\n{'─' * 50}")
    print(f"📊 DOWNLOAD SUMMARY")
    print(f"{'─' * 50}")
    print(f"   Previous products: {len(existing_rows)}")
    print(f"   New products:      {len(new_rows)}")
    print(f"   Total products:    {len(all_rows)}")
    print(f"   New images DL'd:   {success}/{len(new_rows)}")
    print(f"   📁 Images: {IMAGES_DIR}/")
    print(f"   📄 CSV: {OUTPUT_CSV}")
    print(f"\n   Next steps:")
    print(f"     python clean_data.py")
    print(f"     python build_embeddings.py")
    print(f"     python -m streamlit run app.py")


if __name__ == "__main__":
    main()
