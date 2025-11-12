# osm_groomers_by_city.py
import requests, csv, time, re
from pathlib import Path

OVERPASS_URLS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
    "https://overpass.nchc.org.tw/api/interpreter",
    "https://overpass.osm.ch/api/interpreter",
]

CITIES = [
    ("Miami", 25.7617, -80.1918, 45),
    ("Fort Lauderdale", 26.1224, -80.1373, 35),
    ("West Palm Beach", 26.7153, -80.0534, 35),
    ("Boca Raton", 26.3683, -80.1289, 30),
    ("Orlando", 28.5383, -81.3792, 40),
    ("Tampa", 27.9506, -82.4572, 40),
    ("St Petersburg", 27.7676, -82.6403, 35),
    ("Clearwater", 27.9659, -82.8001, 30),
    ("Jacksonville", 30.3322, -81.6557, 45),
    ("Sarasota", 27.3364, -82.5307, 35),
    ("Naples", 26.1420, -81.7948, 35),
    ("Fort Myers", 26.6406, -81.8723, 35),
    ("Lakeland", 28.0395, -81.9498, 30),
    ("Daytona Beach", 29.2108, -81.0228, 30),
    ("Ocala", 29.1872, -82.1401, 30),
    ("Gainesville", 29.6516, -82.3248, 30),
    ("Tallahassee", 30.4383, -84.2807, 35),
    ("Pensacola", 30.4213, -87.2169, 35),
    ("Port St. Lucie", 27.2730, -80.3582, 30),
    ("Melbourne", 28.0836, -80.6081, 30),
]

OUT = "fl_pet_groomers_osm.csv"

MOBILE_KEYWORDS = [
    "mobile pet grooming", "mobile dog grooming", "mobile grooming",
    "we come to you", "house call", "grooming van", "mobile salon", "at your home"
]

def normalize_phone(p: str) -> str:
    return re.sub(r"[^0-9+]", "", p or "")

def looks_mobile(text: str) -> bool:
    t = (text or "").lower()
    return any(k in t for k in MOBILE_KEYWORDS)

def first_nonempty(tags: dict, *keys):
    for k in keys:
        v = tags.get(k)
        if v: return v
    return ""

def city_query(lat: float, lon: float, radius_km: int) -> str:
    meters = int(radius_km * 1000)
    return rf"""
[out:json][timeout:120];
(
  node["shop"="pet_grooming"](around:{meters},{lat},{lon});
  way["shop"="pet_grooming"](around:{meters},{lat},{lon});
  relation["shop"="pet_grooming"](around:{meters},{lat},{lon});

  node["name"~"(?i)mobile.*groom|groom.*mobile"](around:{meters},{lat},{lon});
  way["name"~"(?i)mobile.*groom|groom.*mobile"](around:{meters},{lat},{lon});
  relation["name"~"(?i)mobile.*groom|groom.*mobile"](around:{meters},{lat},{lon});

  node["description"~"(?i)mobile.*groom"](around:{meters},{lat},{lon});
  way["description"~"(?i)mobile.*groom"](around:{meters},{lat},{lon});
  relation["description"~"(?i)mobile.*groom"](around:{meters},{lat},{lon});

  node["mobile"~"(?i)yes|true"](around:{meters},{lat},{lon});
  way["mobile"~"(?i)yes|true"](around:{meters},{lat},{lon});
  relation["mobile"~"(?i)yes|true"](around:{meters},{lat},{lon});

  node["service:mobile"~"(?i)yes|true"](around:{meters},{lat},{lon});
  way["service:mobile"~"(?i)yes|true"](around:{meters},{lat},{lon});
  relation["service:mobile"~"(?i)yes|true"](around:{meters},{lat},{lon});
);
out center tags;
"""

def fetch_overpass(query: str, max_retries: int = 8):
    for attempt in range(max_retries):
        url = OVERPASS_URLS[attempt % len(OVERPASS_URLS)]
        try:
            r = requests.post(url, data={"data": query}, timeout=180)
            if r.status_code in (429, 502, 503, 504):
                time.sleep(1.5 * (attempt + 1))
                continue
            r.raise_for_status()
            return r.json()
        except requests.RequestException:
            time.sleep(1.5 * (attempt + 1))
    return None

def ensure_header(path: str, headers: list):
    newfile = not Path(path).exists()
    f = open(path, "a", newline="", encoding="utf-8")
    writer = csv.DictWriter(f, fieldnames=headers)
    if newfile:
        writer.writeheader()
    return f, writer

def main():
    headers = ["source","name","phone","website","address","city","lat","lng","is_mobile_guess"]
    f, writer = ensure_header(OUT, headers)
    written = 0

    for (city_name, lat, lon, radius_km_start) in CITIES:
        radius_km = radius_km_start
        success = False

        for _ in range(4):  # shrink radius if busy
            q = city_query(lat, lon, radius_km)
            print(f"[{city_name}] radius {radius_km}km …")
            data = fetch_overpass(q)
            if not data:
                radius_km = max(10, int(radius_km * 0.65))
                continue

            elements = data.get("elements", [])
            print(f"  -> {len(elements)} elements")
            if not elements and radius_km > 12:
                radius_km = max(10, int(radius_km * 0.65))
                continue

            seen = set()
            for el in elements:
                tags = el.get("tags", {}) or {}
                c_lat = el.get("lat") or (el.get("center", {}) or {}).get("lat") or ""
                c_lon = el.get("lon") or (el.get("center", {}) or {}).get("lon") or ""

                name = first_nonempty(tags, "name")
                phone = normalize_phone(first_nonempty(tags, "contact:phone", "phone"))
                website = first_nonempty(tags, "contact:website", "website", "url")
                street = first_nonempty(tags, "addr:street")
                housenumber = first_nonempty(tags, "addr:housenumber")
                city = first_nonempty(tags, "addr:city") or city_name
                postcode = first_nonempty(tags, "addr:postcode")

                address = ", ".join([s for s in [f"{housenumber} {street}".strip(), city, "FL", postcode] if s])
                tag_text = " ".join([str(v) for v in tags.values()])
                mobile_guess = looks_mobile(f"{name} {website} {tag_text}")

                key = (name or "", phone or "", city or "")
                if key in seen:
                    continue
                seen.add(key)

                row = {
                    "source": "OSM",
                    "name": name,
                    "phone": phone,
                    "website": website,
                    "address": address,
                    "city": city,
                    "lat": c_lat,
                    "lng": c_lon,
                    "is_mobile_guess": mobile_guess
                }
                writer.writerow(row)
                written += 1

            success = True
            break

        if not success:
            print(f"  -> overpass still busy for {city_name}, skipping for now")

        time.sleep(1.2)

    f.close()
    print(f"Saved/updated {OUT} with {written} new rows")

if __name__ == "__main__":
    main()
