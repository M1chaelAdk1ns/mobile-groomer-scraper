import requests
from bs4 import BeautifulSoup
import pandas as pd

# Simple test to confirm everything works end-to-end.
SEARCH_URL = "https://httpbin.org/html"

def main():
    print(f"Requesting {SEARCH_URL} ...")
    try:
        resp = requests.get(SEARCH_URL, timeout=10)
        resp.raise_for_status()
    except Exception as e:
        print("Request failed:", e)
        return

    soup = BeautifulSoup(resp.text, "html.parser")

    # Grab some headings and paragraphs just as a demo
    headings = [h.get_text(strip=True) for h in soup.find_all("h1")]
    paragraphs = [p.get_text(strip=True) for p in soup.find_all("p")]

    data = []
    for h in headings:
        data.append({"type": "heading", "text": h})
    for p in paragraphs:
        data.append({"type": "paragraph", "text": p})

    df = pd.DataFrame(data)
    df.to_csv("test_output.csv", index=False)
    print(f"Saved {len(df)} rows to test_output.csv")

if __name__ == "__main__":
    main()
