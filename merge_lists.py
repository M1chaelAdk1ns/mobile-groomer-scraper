# merge_lists.py
import os, pandas as pd

def load_csv(path):
    df = pd.read_csv(path)
    df = df.rename(columns={"name":"Name","phone":"Phone","address":"Address","city":"City","website":"Website"})
    for col in ["Name","Phone","Address","City","Website"]:
        if col not in df.columns: df[col] = ""
    if "state" not in df.columns: df["state"] = "FL"
    return df[["Name","Phone","Address","City","state","Website"]]

parts = []
if os.path.exists("fl_mobile_groomers_clean.csv"):
    parts.append(load_csv("fl_mobile_groomers_clean.csv"))
if os.path.exists("fl_mobile_groomers_foursquare.csv"):
    parts.append(load_csv("fl_mobile_groomers_foursquare.csv"))

if not parts:
    raise SystemExit("No input CSVs found.")

df = pd.concat(parts, ignore_index=True)
df["Phone"] = df["Phone"].astype(str).str.replace(r"[^0-9+]", "", regex=True)
df = df[(df["Name"].astype(str) != "") & (df["Phone"].astype(str) != "")]
df = df.drop_duplicates(subset=["Name","Phone"])
df.to_csv("fl_mobile_groomers_all.csv", index=False)
print(f"Saved {len(df)} rows to fl_mobile_groomers_all.csv")
