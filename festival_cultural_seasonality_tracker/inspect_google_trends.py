
import pandas as pd
from pathlib import Path

path = Path("data/google_trends_festival.csv")

if not path.exists():
    print("CSV not found. Check the filename and data folder.")
    raise SystemExit

df = pd.read_csv(path)

print("\n========== GOOGLE TRENDS DATA ==========")

print("\nRows:", len(df))
print("\nColumns:", df.columns.tolist())

print("\nFirst 15 rows:")
print(df.head(15).to_string(index=False))

print("\nLast 10 rows:")
print(df.tail(10).to_string(index=False))

print("\nMissing values:")
print(df.isna().sum().to_string())

print("\nData types:")
print(df.dtypes.to_string())

print("\nDataset information:")
print(df.info())

print("\n========== INSPECTION COMPLETE ==========")
