# clean_osm_mobile.py
import re, time, requests, pandas as pd
from bs4 import BeautifulSoup

IN_FILE = "fl_pet_groomers_osm.csv"
OUT_FILE = "fl_mobile_groomers_clean.csv"

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
KEYWORDS = [
    "mobile grooming", "mobile pet grooming", "mobile dog grooming",
    "we come to you", "house call", "grooming van", "mobile salon", "at your home"
]
MAX_FETCH = 200

def looks_mobile(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in KEYWORDS)

def normalize_phone(p: str) -> str:
    nums = re.sub(r"[^0-9+]", "", p or "")
    return nums if len(nums) >= 10 else ""

def fetch_text(url: str) -> str:
    try:
        r = requests.get(url, headers=HEADERS, timeout=12)
        if r.status_code != 200 or "text/html" not in r.headers.get("Content-Type",""):
            return ""
        soup = BeautifulSoup(r.text, "html.parser")
        return soup.get_text(" ", strip=True)[:50000]
    except Exception:
        return ""

def main():
    df = pd.read_csv(IN_FILE).copy()
    df["phone"] = df["phone"].astype(str).apply(normalize_phone)
    if "is_mobile_guess" not in df.columns:
        df["is_mobile_guess"] = False
    df["is_mobile_guess"] = df["is_mobile_guess"].fillna(False)

    to_check_mask = (~df["website"].isna()) & (df["website"].astype(str) != "") & (~df["is_mobile_guess"])
    to_check = df[to_check_mask].copy()

    checked = 0
    for idx, row in to_check.iterrows():
        if checked >= MAX_FETCH: break
        text = fetch_text(str(row["website"]))
        if looks_mobile(text):
            df.loc[idx, "is_mobile_guess"] = True
        checked += 1
        time.sleep(0.6)

    name_has_mobile = df["name"].astype(str).str.contains("mobile", case=False, na=False)
    site_has_mobile = df["website"].astype(str).str.contains("mobile|house call|van|we come to you", case=False, na=False)

    keep_mask = (df["phone"] != "") & (df["is_mobile_guess"] | name_has_mobile | site_has_mobile)
    keep = df.loc[keep_mask].copy()

    if keep.empty:
        print("No strong mobile matches—try re-running after the scraper collects more.")
        return

    keep["priority_score"] = 3 + keep["website"].notna().astype(int) + (keep["city"].astype(str) != "").astype(int)

    out = keep.copy()
    out["state"] = "FL"
    out.rename(columns={"name":"Name","phone":"Phone","address":"Address","city":"City","website":"Website"}, inplace=True)
    out = out[["Name","Phone","Address","City","state","Website","priority_score"]]
    out = out.drop_duplicates(subset=["Name","Phone"]).sort_values("priority_score", ascending=False)

    out.to_csv(OUT_FILE, index=False)
    print(f"Saved {len(out)} rows to {OUT_FILE}")

if __name__ == "__main__":
    main()
