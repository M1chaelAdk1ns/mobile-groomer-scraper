import requests
from bs4 import BeautifulSoup
import pandas as pd

# TEMP TEST:
# This is just to prove your environment works.
# We'll swap this for a real directory/search next.
SEARCH_URL = "https://example.com"

def main():
    resp = requests.get(SEARCH_URL, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    # Grab all <h1> and <p> just as a dumb demo
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
