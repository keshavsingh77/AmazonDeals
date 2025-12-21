from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import requests
from bs4 import BeautifulSoup
import re

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def clean_price(price_str):
    if not price_str: return 0
    clean = re.sub(r'[^\d.]', '', str(price_str))
    try: return float(clean)
    except: return 0

@app.get("/api/check")
def check_price(url: str, tag: str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9",
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=10, allow_redirects=True)
        if response.status_code != 200: return {"error": "Link Blocked"}

        final_url = response.url
        match = re.search(r'/dp/([A-Z0-9]{10})', final_url)
        if not match: match = re.search(r'/gp/product/([A-Z0-9]{10})', final_url)
        if not match: match = re.search(r'/([A-Z0-9]{10})', final_url)

        if not match: return {"error": "Product ID Not Found"}
        asin = match.group(1)
        
        affiliate_link = f"https://www.amazon.in/dp/{asin}?tag={tag}"

        soup = BeautifulSoup(response.content, "lxml")

        # 1. Title & Image
        title = soup.find("span", attrs={"id": "productTitle"})
        title = title.get_text().strip()[:60] + "..." if title else "Amazon Deal"

        image = "https://placehold.co/200?text=No+Image"
        img_div = soup.find("div", attrs={"id": "imgTagWrapperId"})
        if img_div and img_div.find("img"): image = img_div.find("img")["src"]
        else:
            landing_img = soup.find("img", attrs={"id": "landingImage"})
            if landing_img: image = landing_img["src"]

        # 2. Price Logic
        price_tag = soup.find("span", attrs={"class": "a-price-whole"})
        if not price_tag: price_tag = soup.find("span", attrs={"class": "a-offscreen"})
        
        selling_price_str = "Check"
        selling_price_val = 0
        if price_tag:
            raw_price = price_tag.get_text().strip().replace('.', '')
            selling_price_str = "₹" + raw_price if "₹" not in raw_price else raw_price
            selling_price_val = clean_price(selling_price_str)

        # 3. MRP & Discount Logic
        mrp_str = ""
        discount_str = ""
        mrp_tag = soup.find("span", attrs={"class": "a-text-price"})
        if mrp_tag:
            mrp_inner = mrp_tag.find("span", attrs={"class": "a-offscreen"})
            if mrp_inner:
                mrp_str = mrp_inner.get_text().strip()
                mrp_val = clean_price(mrp_str)
                if mrp_val > selling_price_val and mrp_val > 0:
                    off = int(((mrp_val - selling_price_val) / mrp_val) * 100)
                    if off > 0: discount_str = f"-{off}%"

        # 4. COUPON CHECK (New)
        # Amazon pe coupon aksar 'Apply ₹100 coupon' likha hota hai
        coupon_text = ""
        coupon_elem = soup.find("label", string=re.compile(r"Apply .* coupon"))
        if not coupon_elem:
            # Alternate search
            coupon_elem = soup.find("span", class_="promoPriceBlockMessage")
        
        if coupon_elem:
            # Text saaf karo "Apply ₹50 coupon"
            full_text = coupon_elem.get_text().strip()
            # Sirf amount nikalne ki koshish (e.g. ₹50)
            amount_match = re.search(r'(₹\d+|SAVE \d+)', full_text)
            if amount_match:
                coupon_text = f"Apply {amount_match.group(0)} Coupon"
            else:
                coupon_text = "Coupon Available"

        # 5. BANK OFFER CHECK (Generic)
        bank_offer = False
        # Pure page text me 'Bank Offer' dhoondo
        if "Bank Offer" in soup.get_text():
            bank_offer = True

        return {
            "title": title,
            "price": selling_price_str,
            "mrp": mrp_str,
            "discount": discount_str,
            "coupon": coupon_text, # New Data
            "bank_offer": bank_offer, # New Data
            "image": image,
            "link": affiliate_link
        }

    except Exception as e:
        return {"error": str(e)}
