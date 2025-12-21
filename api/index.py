from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import re
import random

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mobile Headers (kam block hote hain)
user_agents = [
    "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 13; SM-S908B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36"
]

def clean_price(price_str):
    if not price_str: return 0
    clean = re.sub(r'[^\d.]', '', str(price_str))
    try: return float(clean)
    except: return 0

@app.get("/api/check")
def check_price(url: str, tag: str):
    # FALLBACK DATA (Agar scraping fail hui to ye dikhega)
    fallback_data = {
        "title": "Shop Now on Amazon",
        "price": "Check Price",
        "mrp": "",
        "discount": "",
        "coupon": "",
        "bank_offer": False,
        "image": "https://upload.wikimedia.org/wikipedia/commons/a/a9/Amazon_logo.svg", # Clean Logo
        "link": url 
    }

    try:
        session = requests.Session()
        headers = {
            "User-Agent": random.choice(user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Referer": "https://www.google.com/"
        }

        # 1. Resolve Link
        response = session.get(url, headers=headers, timeout=8, allow_redirects=True)
        
        # Agar Amazon ne block kiya (503/404) to Fallback return karo
        if response.status_code != 200:
            # Link fix karke return karo
            fallback_data["link"] = url 
            return fallback_data

        final_url = response.url
        match = re.search(r'/(dp|gp/product)/([A-Z0-9]{10})', final_url)
        asin = match.group(2) if match else "UNKNOWN"
        
        affiliate_link = f"https://www.amazon.in/dp/{asin}?tag={tag}" if asin != "UNKNOWN" else final_url
        fallback_data["link"] = affiliate_link

        soup = BeautifulSoup(response.content, "lxml")

        # --- DATA EXTRACTION ---
        
        # Title
        title = None
        if not title:
            meta = soup.find("meta", attrs={"name": "title"})
            if meta: title = meta.get('content')
        if not title:
            og = soup.find("meta", property="og:title")
            if og: title = og.get('content')
        if not title:
            span = soup.find("span", attrs={"id": "productTitle"})
            if span: title = span.get_text().strip()
        
        if title:
            title = title.replace("Amazon.in:", "").replace("Buy ", "").strip()
            fallback_data["title"] = title[:75] + "..."

        # Image
        image = None
        if not image:
            og_img = soup.find("meta", property="og:image")
            if og_img: image = og_img.get('content')
        if not image:
            landing = soup.find("img", attrs={"id": "landingImage"})
            if landing: image = landing.get("src")
        
        if image:
            fallback_data["image"] = image

        # Price
        price_tag = soup.find("span", attrs={"class": "a-price-whole"})
        if not price_tag: price_tag = soup.find("span", attrs={"class": "a-offscreen"})
        
        selling_price_val = 0
        if price_tag:
            raw_price = price_tag.get_text().strip().replace('.', '')
            fallback_data["price"] = "₹" + raw_price
            selling_price_val = clean_price(fallback_data["price"])

        # MRP & Discount
        mrp_tag = soup.find("span", attrs={"class": "a-text-price"})
        if mrp_tag:
            mrp_inner = mrp_tag.find("span", attrs={"class": "a-offscreen"})
            if mrp_inner:
                mrp_str = mrp_inner.get_text().strip()
                fallback_data["mrp"] = mrp_str
                mrp_val = clean_price(mrp_str)
                if mrp_val > selling_price_val and mrp_val > 0:
                    off = int(((mrp_val - selling_price_val) / mrp_val) * 100)
                    if off > 0: fallback_data["discount"] = f"-{off}%"

        # Offers
        page_text = soup.get_text()
        if "Apply" in page_text and "coupon" in page_text:
            fallback_data["coupon"] = "Coupon Available"
        
        if "Bank Offer" in page_text or "Partner Offers" in page_text:
            fallback_data["bank_offer"] = True

        return fallback_data

    except Exception:
        # Agar kuch bhi fat'ta hai, to Safe Data return kar do
        return fallback_data
