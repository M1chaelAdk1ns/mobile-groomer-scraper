import requests
from bs4 import BeautifulSoup
import pandas as pd

SEARCH_URL = "https://example.com/search"  # placeholder

def main():
    resp = requests.get(SEARCH_URL, timeout=15)
    soup = BeautifulSoup(resp.text, "html.parser")
    listings = soup.select(".listing")  # placeholder selector

    rows = []
    for block in listings:
        name = block.get_text(strip=True)
        if name:
            rows.append({"name": name})

    df = pd.DataFrame(rows)
    df.to_csv("test_mobile_groomers.csv", index=False)
    print(f"Saved {len(df)} rows")

if __name__ == "__main__":
    main()
