import requests
from bs4 import BeautifulSoup
import pandas as pd

# Simple connectivity + parsing test
TEST_URL = "https://httpbin.org/html"

def main():
    resp = requests.get(TEST_URL, timeout=10)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")
    heading = soup.find("h1").get_text(strip=True)

    df = pd.DataFrame([{"type": "heading", "text": heading}])
    df.to_csv("test_output.csv", index=False)
    print("Saved test_output.csv with", len(df), "row")

if __name__ == "__main__":
    main()
