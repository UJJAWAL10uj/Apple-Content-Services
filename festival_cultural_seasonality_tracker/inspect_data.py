import pandas as pd
from pathlib import Path

path = Path("data/app_chart_snapshots.csv")

if not path.exists():
    print("ERROR: CSV file not found.")
    raise SystemExit

df = pd.read_csv(path)

print("\n========== DATASET OVERVIEW ==========")
print("Total rows:", len(df))
print("Total columns:", len(df.columns))

print("\n========== COLUMN NAMES ==========")
for col in df.columns:
    print("-", col)

print("\n========== FIRST 8 RECORDS ==========")
print(df.head(8).to_string(index=False))

print("\n========== MISSING VALUES ==========")
print(df.isnull().sum().to_string())

print("\n========== UNIQUE VALUES ==========")
for col in df.columns:
    if df[col].nunique() <= 20:
        print(f"\n{col}:")
        print(df[col].value_counts(dropna=False).to_string())

print("\n========== DATA TYPES ==========")
print(df.dtypes.to_string())

print("\n========== INSPECTION COMPLETE ==========")