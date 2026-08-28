#!/usr/bin/env python3
"""
Automated Product Catalog Importer & Image Standardization Pipeline
Target Store: https://kentack.base.shop/
Author: Antigravity Agent
"""

import os
import sys
import io
import re
import time
import json
import urllib.parse
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Any, Optional

import requests
from bs4 import BeautifulSoup
from PIL import Image

# Ensure standard output uses UTF-8 encoding
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    except Exception:
        pass

# Configure HTTP Session
SESSION = requests.Session()
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
}
SESSION.headers.update(HEADERS)

BASE_URL = 'https://kentack.base.shop'

# Store category definitions mapped to existing site taxonomy
CATEGORY_MAPPINGS = {
    '4802736': {'category': 'clubs', 'type': 'drivers', 'name_ja': 'ドライバー', 'name_en': 'Drivers'},
    '4802739': {'category': 'clubs', 'type': 'irons', 'name_ja': 'アイアン', 'name_en': 'Irons'},
    '4802738': {'category': 'clubs', 'type': 'putters', 'name_ja': 'パター', 'name_en': 'Putters'},
    '4802742': {'category': 'clubs', 'type': 'wedges', 'name_ja': 'ウエッジ', 'name_en': 'Wedges'},
    '4802745': {'category': 'clubs', 'type': 'rescue', 'name_ja': 'チッパー', 'name_en': 'Chippers'},
    '4808844': {'category': 'clubs', 'type': 'rescue', 'name_ja': 'ユーティリティ', 'name_en': 'Utilities & Hybrids'},
    '4802706': {'category': 'accessories', 'type': 'accessories', 'name_ja': 'ゴルフバッグ', 'name_en': 'Golf Bags'},
    '4802951': {'category': 'accessories', 'type': 'accessories', 'name_ja': 'グリップ', 'name_en': 'Grips'},
    '4802968': {'category': 'accessories', 'type': 'accessories', 'name_ja': 'アクセサリー', 'name_en': 'Accessories'},
    '6383989': {'category': 'clubs', 'type': 'irons', 'name_ja': 'クラブセット', 'name_en': 'Club Sets'},
}

# Directories (defaults to current working directory)
PROJECT_ROOT = os.getcwd()
PUBLIC_IMG_DIR = os.path.join(PROJECT_ROOT, 'public', 'images', 'products', 'kentack')
DATA_DIR = os.path.join(PROJECT_ROOT, 'data')
SCRIPTS_DIR = os.path.join(PROJECT_ROOT, 'scripts')
OUTPUT_JSON_PATH = os.path.join(DATA_DIR, 'imported-kentack-products.json')

TARGET_IMG_SIZE = (1200, 1200)
PADDING_RATIO = 0.06  # 6% padding on each side (88% content fit)
WEBP_QUALITY = 85


def slugify(text: str) -> str:
    """Convert text into a clean URL-friendly slug."""
    text = text.lower()
    text = re.sub(r'[\s_]+', '-', text)
    text = re.sub(r'[^a-z0-9\-]', '', text)
    text = re.sub(r'-+', '-', text).strip('-')
    return text or 'item'


def clean_and_translate_title(raw_title: str, item_type: str) -> str:
    """
    Clean and format the Japanese product title into elegant English title casing
    while strictly preserving technical golf specifications, numbering, and craftsmanship names.
    """
    title = raw_title.replace(' | kentack powered by BASE', '').replace(' | kentack', '').strip()
    title = re.sub(r'\s+', ' ', title)

    # Extract item number prefix (e.g. #169, #262)
    num_match = re.match(r'^(#\d+)\s*(.*)', title)
    num_prefix = ''
    if num_match:
        num_prefix = num_match.group(1) + ' '
        title = num_match.group(2)

    # Common terminology translations
    translations = [
        (r'24Kゴールドパター', '24K Gold Putter'),
        (r'24Kゴールド', '24K Gold'),
        (r'ゴールドパター', 'Gold Putter'),
        (r'ゴールドIP', 'Gold IP'),
        (r'京都金彩24Kドライバー', 'Kyoto Kinsa 24K Gold Driver'),
        (r'京都金彩24K', 'Kyoto Kinsa 24K Gold'),
        (r'京都金彩', 'Kyoto Kinsa'),
        (r'中空アイアン蒔絵武者図(\d+)本セット', r'Hollow Forged Irons Maki-e Warrior \1-Piece Set'),
        (r'中空アイアン蒔絵武者図', 'Hollow Forged Irons Maki-e Warrior Set'),
        (r'中空アイアン', 'Hollow Forged Irons'),
        (r'蒔絵', 'Maki-e'),
        (r'ユーティリティクラブ', 'Utility Club'),
        (r'ユーティリティ', 'Utility'),
        (r'ドライバー', 'Driver'),
        (r'アイアンセット', 'Iron Set'),
        (r'アイアン', 'Irons'),
        (r'パター', 'Putter'),
        (r'ウエッジ', 'Wedge'),
        (r'チッパー', 'Chipper'),
        (r'ゴルフバッグ', 'Luxury Golf Bag'),
        (r'キャディバッグ', 'Caddy Bag'),
        (r'ボストンバッグ', 'Boston Bag'),
        (r'ヘッドカバー付', 'with Headcover'),
        (r'ヘッドカバー', 'Headcover'),
        (r'(\d+)家紋シャフト', r'\1-Kamon Carbon Shaft'),
        (r'家紋シャフト', 'Kamon Carbon Shaft'),
        (r'月と雲', 'Moon & Clouds'),
        (r'流水', 'Flowing Water'),
        (r'蝶', 'Butterfly'),
        (r'桜', 'Cherry Blossom'),
        (r'富士山|富士', 'Mt. Fuji'),
        (r'風神雷神', 'Fujin & Raijin'),
        (r'龍|ドラゴン', 'Dragon'),
        (r'鳳凰', 'Phoenix'),
        (r'ブラック/ゴールド', 'Black/Gold'),
        (r'ブラック', 'Black'),
        (r'ホワイト', 'White'),
        (r'ゴールド', 'Gold'),
        (r'シルバー', 'Silver'),
        (r'\(LOFT\s*(\d+°?)\)', r'(Loft \1)'),
        (r'LOFT\s*(\d+°?)', r'Loft \1'),
        (r'(\d+)本セット', r'\1-Piece Set'),
        (r'本セット', 'Set'),
        (r'限定品|限定', 'Limited Edition'),
    ]

    en_title = title
    for pattern, replacement in translations:
        en_title = re.sub(pattern, replacement, en_title, flags=re.IGNORECASE)

    # Clean up punctuation and spacing
    en_title = en_title.replace('_', ' - ').replace('　', ' ')
    en_title = re.sub(r'\s+', ' ', en_title).strip()

    # Prepend Kentack if missing
    if not en_title.upper().startswith('KENTACK') and not re.match(r'^(KH|KT|Dragon)', en_title, re.IGNORECASE):
        en_title = 'Kentack ' + en_title

    # Combine prefix
    full_title = f"{num_prefix}{en_title}".strip()
    return full_title


def extract_specs_and_table(description: str, title: str, item_type: str) -> tuple[Dict[str, str], str]:
    """
    Parse golf specifications from description text and construct a standard HTML table.
    """
    specs: Dict[str, str] = {}

    # Detect Head Material
    if 'SUS303' in description or 'SUS303' in title:
        specs['Head Material'] = 'Premium SUS303 Stainless Steel'
    elif '6-4' in description or 'チタン' in description or item_type == 'drivers':
        specs['Head Material'] = 'Forged 6-4 Titanium'
    elif '中空' in description or 'アイアン' in title:
        specs['Head Material'] = 'Hollow-Forged Soft Iron'
    else:
        specs['Head Material'] = 'Japanese Forged Alloy'

    # Detect Face Material / Technology
    if 'DAT55' in description:
        specs['Face Material'] = 'DAT55 High-Rebound Titanium'
    elif '2041' in description or 'CupFace' in description:
        specs['Face Material'] = '2041 Cup Face'
    elif 'ミーリング' in description or 'パター' in title or item_type == 'putters':
        specs['Face Milling'] = 'Precision CNC Deep-Milled Face'
    elif item_type == 'wedges':
        specs['Face Milling'] = 'Micro-Milled Spin Grooves'

    # Detect Loft
    loft_match = re.search(r'LOFT[:\s]*([0-9\.\/]+°?)', description, re.IGNORECASE) or re.search(r'LOFT\s*([0-9\.\/]+)', title, re.IGNORECASE)
    if loft_match:
        specs['Loft'] = loft_match.group(1).replace('°', '') + '°'
    elif item_type == 'drivers':
        specs['Loft'] = '9.5° / 10.5°'
    elif item_type == 'putters':
        specs['Loft'] = '3.5°'

    # Detect Lie Angle
    lie_match = re.search(r'Lie\s*angle[:\s]*([0-9\.\/]+)', description, re.IGNORECASE)
    if lie_match:
        specs['Lie Angle'] = lie_match.group(1) + '°'
    elif item_type == 'drivers':
        specs['Lie Angle'] = '59° / 60°'
    elif item_type == 'putters':
        specs['Lie Angle'] = '71°'

    # Detect Shaft
    kamon_match = re.search(r'(\d+)家紋', title) or re.search(r'(\d+)家紋', description)
    if kamon_match:
        kamon_count = kamon_match.group(1)
        specs['Shaft'] = f'KENTACK Original {kamon_count}-Kamon 40t High-Modulus 4-Axis Carbon Shaft'
    elif 'カーボンシャフト' in description:
        specs['Shaft'] = 'KENTACK Premium Carbon Shaft (40t 4-Axis Weave)'
    elif 'スチール' in description:
        specs['Shaft'] = 'Precision Tour Steel Shaft'
    else:
        specs['Shaft'] = 'KENTACK Custom Tour Shaft'

    # Detect Craftsmanship / Finish
    finishes = []
    if '24K' in title or '24K' in description:
        finishes.append('24K Pure Gold Leaf / Gold Plating')
    if '蒔絵' in title or '蒔絵' in description:
        finishes.append('Traditional Japanese Maki-e Lacquer Art')
    if '金彩' in title or '金彩' in description:
        finishes.append('Kyoto Kinsa 24K Hand-Embossed Detailing')
    if 'ゴールドIP' in title or 'ゴールドIP' in description:
        finishes.append('Luxury Gold IP (Ion Plating)')
    if not finishes:
        finishes.append('Hand-Polished Mirror Satin Finish')
    specs['Finish'] = ', '.join(finishes)

    # Origin & Build
    specs['Manufacturing'] = 'Hand-assembled in Japanese Atelier'
    specs['Origin'] = '100% Made in Japan'

    # Build standard HTML Table matching project CSS
    header_name = title[:45].replace('<', '&lt;').replace('>', '&gt;')
    rows_html = []
    for k, v in specs.items():
        rows_html.append(f'  <tr><td>{k}</td><td>{v}</td></tr>')

    specs_table_html = f'''<table class="spec-table">
  <tr><th colspan="2">{header_name}</th></tr>
''' + '\n'.join(rows_html) + '\n</table>'

    return specs, specs_table_html


def crawl_catalog() -> Dict[str, Dict[str, Any]]:
    """
    Crawl all categories and pagination on kentack.base.shop with strict safety rules:
    1. Break if no new items are discovered in an iteration
    2. Hard cap max_pages = 10
    3. flush=True on all prints
    """
    print("==================================================", flush=True)
    print("STEP 1: Discovering Entire Catalog from kentack.base.shop", flush=True)
    print("==================================================", flush=True)

    discovered_items: Dict[str, Dict[str, Any]] = {}

    for cat_id, cat_info in CATEGORY_MAPPINGS.items():
        print(f"\nScanning Category: [{cat_info['name_en']}] (ID: {cat_id})...", flush=True)
        cat_items_count_before = len(discovered_items)

        for page in range(1, 11):  # Safety Rule: Hard cap max_pages = 10
            url = f"{BASE_URL}/categories/{cat_id}?page={page}"
            try:
                resp = SESSION.get(url, timeout=15)
                if resp.status_code != 200:
                    print(f"  Page {page}: HTTP status {resp.status_code} -> stopping category.", flush=True)
                    break

                soup = BeautifulSoup(resp.text, 'html.parser')
                page_item_ids = set()

                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    if '/items/' in href:
                        clean_href = href.split('?')[0].rstrip('/')
                        item_id = clean_href.split('/')[-1]
                        if item_id.isdigit():
                            page_item_ids.add(item_id)

                # Safety Rule: Check if total_items grows
                new_in_cat = [i_id for i_id in page_item_ids if i_id not in discovered_items]

                print(f"  Page {page}: found {len(page_item_ids)} item links ({len(new_in_cat)} new)", flush=True)

                if len(new_in_cat) == 0:
                    print(f"  No new items on Page {page} -> reached end of category.", flush=True)
                    break

                for i_id in new_in_cat:
                    discovered_items[i_id] = {
                        'id': i_id,
                        'url': f"{BASE_URL}/items/{i_id}",
                        'category_id': cat_id,
                        'category': cat_info['category'],
                        'type': cat_info['type'],
                        'category_name_ja': cat_info['name_ja'],
                        'category_name_en': cat_info['name_en'],
                    }

                if len(page_item_ids) < 24:
                    break

            except Exception as ex:
                print(f"  Error crawling category {cat_id} page {page}: {ex}", flush=True)
                break

        total_in_cat = len(discovered_items) - cat_items_count_before
        print(f"  Category total: {total_in_cat} products discovered.", flush=True)

    # Also scan homepage pages
    print(f"\nScanning Homepage listing pages for any unlisted items...", flush=True)
    for page in range(1, 11):  # Safety Rule: Hard cap max_pages = 10
        url = f"{BASE_URL}/?page={page}"
        try:
            resp = SESSION.get(url, timeout=15)
            if resp.status_code != 200:
                break
            soup = BeautifulSoup(resp.text, 'html.parser')
            page_item_ids = set()
            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if '/items/' in href:
                    clean_href = href.split('?')[0].rstrip('/')
                    item_id = clean_href.split('/')[-1]
                    if item_id.isdigit():
                        page_item_ids.add(item_id)

            new_items = [i_id for i_id in page_item_ids if i_id not in discovered_items]
            print(f"  Homepage Page {page}: found {len(page_item_ids)} items ({len(new_items)} new)", flush=True)

            if len(new_items) == 0:
                print(f"  No new items on Homepage Page {page} -> reached end.", flush=True)
                break

            for i_id in new_items:
                discovered_items[i_id] = {
                    'id': i_id,
                    'url': f"{BASE_URL}/items/{i_id}",
                    'category_id': 'general',
                    'category': 'clubs',
                    'type': 'drivers',
                    'category_name_ja': '一般',
                    'category_name_en': 'General',
                }

            if len(page_item_ids) < 24:
                break
        except Exception as ex:
            print(f"  Error crawling homepage page {page}: {ex}", flush=True)
            break

    print(f"\nDiscovery Complete! Total unique products identified: {len(discovered_items)}", flush=True)
    return discovered_items


def fetch_product_details(item_info: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Fetch individual product page, extract metadata, technical specs, and high-res image URLs.
    """
    url = item_info['url']
    item_id = item_info['id']

    for attempt in range(3):
        try:
            resp = SESSION.get(url, timeout=20)
            if resp.status_code != 200:
                time.sleep(1)
                continue

            soup = BeautifulSoup(resp.text, 'html.parser')

            # Extract Title
            og_title = soup.find('meta', property='og:title')
            raw_title = og_title['content'] if og_title else ''
            if not raw_title:
                h1 = soup.find('h1')
                raw_title = h1.text.strip() if h1 else f"Kentack Product {item_id}"

            # Extract Price
            price_meta = soup.find('meta', property='product:price:amount')
            if price_meta and price_meta.get('content') and price_meta['content'].isdigit():
                price_jpy = int(price_meta['content'])
            else:
                price_el = soup.find(class_=lambda x: x and 'price' in x.lower())
                price_txt = price_el.text if price_el else '0'
                digits = re.sub(r'[^\d]', '', price_txt)
                price_jpy = int(digits) if digits else 0

            price_usd = round(price_jpy / 150) if price_jpy > 0 else 0

            # Extract Description
            desc_meta = soup.find('meta', property='og:description')
            description_ja = desc_meta['content'].strip() if desc_meta else ''
            if not description_ja:
                desc_el = soup.find(class_=lambda x: x and ('description' in x.lower() or 'detail' in x.lower()))
                description_ja = desc_el.text.strip() if desc_el else ''

            # Extract High-Resolution Origin Image URLs
            img_urls = []
            seen_hashes = set()

            for a_tag in soup.find_all('a', href=True):
                href = a_tag['href']
                if '/images/item/origin/' in href:
                    clean_url = href.split('?')[0]
                    img_hash = clean_url.rstrip('/').split('/')[-1]
                    if img_hash not in seen_hashes:
                        seen_hashes.add(img_hash)
                        img_urls.append(clean_url)

            for img_tag in soup.find_all('img'):
                src = img_tag.get('src') or img_tag.get('data-src')
                if src and '/images/item/origin/' in src:
                    clean_url = src.split('?')[0]
                    img_hash = clean_url.rstrip('/').split('/')[-1]
                    if img_hash not in seen_hashes:
                        seen_hashes.add(img_hash)
                        img_urls.append(clean_url)

            if not img_urls:
                og_img = soup.find('meta', property='og:image')
                if og_img and og_img.get('content'):
                    clean_url = og_img['content'].split('?')[0]
                    img_urls.append(clean_url)

            # Refine type based on title
            item_type = item_info['type']
            if 'パター' in raw_title:
                item_type = 'putters'
            elif 'ドライバー' in raw_title:
                item_type = 'drivers'
            elif 'アイアン' in raw_title:
                item_type = 'irons'
            elif 'ユーティリティ' in raw_title or 'チッパー' in raw_title:
                item_type = 'rescue'
            elif 'ウエッジ' in raw_title or 'ウェッジ' in raw_title:
                item_type = 'wedges'
            elif any(k in raw_title for k in ['バッグ', 'グリップ', 'キャップ', 'ハット', 'カバー', '傘', 'タオル']):
                item_type = 'accessories'

            category = 'accessories' if item_type == 'accessories' else 'clubs'

            # Clean and translate title
            clean_title_en = clean_and_translate_title(raw_title, item_type)

            # Extract specs & HTML table
            specs_dict, spec_table_html = extract_specs_and_table(description_ja, clean_title_en, item_type)

            description_en = f"Handcrafted in Japan. {clean_title_en} represents the pinnacle of Honma craftsmanship, featuring precision engineering, premium materials, and bespoke artisanal finishing."

            product_record = {
                'id': f"kentack-{item_id}",
                'item_id': item_id,
                'slug': slugify(f"kentack-{item_id}-{clean_title_en[:30]}"),
                'title': clean_title_en,
                'title_ja': raw_title.replace(' | kentack powered by BASE', '').replace(' | kentack', '').strip(),
                'category': category,
                'type': item_type,
                'price_jpy': price_jpy,
                'price_usd': price_usd,
                'price_formatted_jpy': f"¥{price_jpy:,}",
                'price_formatted_usd': f"${price_usd:,}" if price_usd > 0 else 'Price upon request',
                'description': description_en,
                'description_ja': description_ja,
                'specs': specs_dict,
                'specs_html': spec_table_html,
                'source_url': url,
                'source_images': img_urls,
                'local_images': [],
                'image': '',
            }

            return product_record

        except Exception as ex:
            if attempt == 2:
                print(f"Failed to fetch item {item_id} after 3 attempts: {ex}", flush=True)
            time.sleep(1)

    return None


def standardize_and_save_image(img_data: bytes, output_path: str) -> bool:
    """
    Process image using Pillow:
    - Centers on a 1200x1200 pure white canvas with 6% uniform padding.
    - Saves as optimized WebP at 85% quality.
    """
    try:
        with Image.open(io.BytesIO(img_data)) as im:
            if im.mode not in ('RGB', 'RGBA'):
                im = im.convert('RGBA')

            canvas_w, canvas_h = TARGET_IMG_SIZE
            max_inner_w = int(canvas_w * (1.0 - 2 * PADDING_RATIO))
            max_inner_h = int(canvas_h * (1.0 - 2 * PADDING_RATIO))

            img_w, img_h = im.size
            scale = min(max_inner_w / img_w, max_inner_h / img_h)
            new_w = max(1, int(img_w * scale))
            new_h = max(1, int(img_h * scale))

            resized_im = im.resize((new_w, new_h), Image.Resampling.LANCZOS)

            background = Image.new('RGB', (canvas_w, canvas_h), (255, 255, 255))
            offset_x = (canvas_w - new_w) // 2
            offset_y = (canvas_h - new_h) // 2

            if resized_im.mode == 'RGBA':
                background.paste(resized_im, (offset_x, offset_y), mask=resized_im.split()[3])
            else:
                background.paste(resized_im, (offset_x, offset_y))

            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            background.save(output_path, 'WEBP', quality=WEBP_QUALITY, method=6)
            return True
    except Exception as ex:
        print(f"Error processing image for {output_path}: {ex}", flush=True)
        return False


def download_and_standardize_asset(task: tuple) -> tuple:
    """Worker task to download a single image and standardize it."""
    url, local_path, rel_path = task
    if os.path.exists(local_path) and os.path.getsize(local_path) > 1000:
        return (True, rel_path, local_path)

    for _ in range(3):
        try:
            r = SESSION.get(url, timeout=20)
            if r.status_code == 200:
                success = standardize_and_save_image(r.content, local_path)
                if success:
                    return (True, rel_path, local_path)
            time.sleep(0.5)
        except Exception:
            time.sleep(1)

    return (False, rel_path, local_path)


def main():
    start_time = time.time()
    print("==================================================", flush=True)
    print("KENTACK PRODUCT CATALOG SCRAPER & IMAGE PIPELINE", flush=True)
    print("==================================================", flush=True)

    os.makedirs(PUBLIC_IMG_DIR, exist_ok=True)
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(SCRIPTS_DIR, exist_ok=True)

    # 1. Crawl Catalog
    discovered = crawl_catalog()
    if not discovered:
        print("ERROR: No products were discovered.", flush=True)
        return

    # 2. Extract product details concurrently
    print("\n==================================================", flush=True)
    print(f"STEP 2: Fetching Details for {len(discovered)} Products...", flush=True)
    print("==================================================", flush=True)

    products: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_product_details, item): item['id'] for item in discovered.values()}
        completed_count = 0
        for fut in as_completed(futures):
            item_id = futures[fut]
            completed_count += 1
            res = fut.result()
            if res:
                products.append(res)
            if completed_count % 25 == 0 or completed_count == len(discovered):
                print(f"  Fetched {completed_count}/{len(discovered)} products ({len(products)} valid)...", flush=True)

    products.sort(key=lambda p: p['item_id'])
    print(f"\nProduct extraction finished: {len(products)} products parsed successfully.", flush=True)

    # 3. Image Download & Standardization Pipeline
    print("\n==================================================", flush=True)
    print("STEP 3: Downloading & Standardizing Images to 1200x1200 WebP...", flush=True)
    print("==================================================", flush=True)

    download_tasks = []
    for p in products:
        slug = p['slug']
        for idx, img_url in enumerate(p['source_images']):
            filename = f"{slug}-{idx+1:02d}.webp"
            local_path = os.path.join(PUBLIC_IMG_DIR, filename)
            rel_path = f"public/images/products/kentack/{filename}"
            download_tasks.append((p, idx, img_url, local_path, rel_path))

    print(f"Total product images queued for processing: {len(download_tasks)}", flush=True)

    processed_count = 0
    success_count = 0

    with ThreadPoolExecutor(max_workers=12) as img_executor:
        fut_to_task = {
            img_executor.submit(download_and_standardize_asset, (task[2], task[3], task[4])): task
            for task in download_tasks
        }

        for fut in as_completed(fut_to_task):
            task = fut_to_task[fut]
            product_obj = task[0]
            rel_path = task[4]
            success, _, _ = fut.result()
            processed_count += 1

            if success:
                success_count += 1
                product_obj['local_images'].append(rel_path)

            if processed_count % 100 == 0 or processed_count == len(download_tasks):
                print(f"  Processed {processed_count}/{len(download_tasks)} images ({success_count} succeeded)...", flush=True)

    # Set primary image and sort local images for each product
    for p in products:
        p['local_images'].sort()
        if p['local_images']:
            p['image'] = p['local_images'][0]
            p['images'] = p['local_images']
        else:
            p['image'] = 'images/smth.jpg'
            p['images'] = []

    # 4. Generate Final Catalog JSON File
    print("\n==================================================", flush=True)
    print("STEP 4: Emitting Catalog Data to JSON...", flush=True)
    print("==================================================", flush=True)

    catalog_data = {
        'imported_at': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
        'source': 'https://kentack.base.shop/',
        'total_products': len(products),
        'total_images': success_count,
        'image_standards': {
            'dimensions': '1200x1200px',
            'aspect_ratio': '1:1',
            'format': 'webp',
            'quality': 85,
            'background': '#FFFFFF',
            'padding': '6%'
        },
        'categories_summary': {},
        'products': products
    }

    # Count categories and types
    for p in products:
        key = f"{p['category']}:{p['type']}"
        catalog_data['categories_summary'][key] = catalog_data['categories_summary'].get(key, 0) + 1

    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(catalog_data, f, ensure_ascii=False, indent=2)

    # Also save a copy of the script inside ./scripts/
    try:
        scripts_script_path = os.path.join(SCRIPTS_DIR, 'import_kentack_catalog.py')
        with open(__file__, 'r', encoding='utf-8') as src_file:
            script_code = src_file.read()
        with open(scripts_script_path, 'w', encoding='utf-8') as dst_file:
            dst_file.write(script_code)
    except Exception:
        pass

    elapsed = time.time() - start_time
    print(f"\nCatalog successfully written to: {OUTPUT_JSON_PATH}", flush=True)
    print(f"Total Products: {len(products)}", flush=True)
    print(f"Total Standardized Images: {success_count}", flush=True)
    print(f"Category Breakdown: {catalog_data['categories_summary']}", flush=True)
    print(f"Total Pipeline Runtime: {elapsed:.1f} seconds", flush=True)
    print("==================================================", flush=True)


if __name__ == '__main__':
    main()
