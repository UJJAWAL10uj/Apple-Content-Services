
import pandas as pd
from pathlib import Path

FILES = {
    "Festival Calendar": Path("data/festival_calendar.csv"),
    "Google Trends Template": Path("data/google_trends_template.csv"),
    "Google Trends Data": Path("data/google_trends.csv")
}

for name, path in FILES.items():

    print("\n" + "=" * 65)
    print(name.upper())
    print("=" * 65)

    if not path.exists():
        print("FILE NOT FOUND:", path)
        continue

    try:
        df = pd.read_csv(path)

        print("\nRows:", len(df))
        print("Columns:", len(df.columns))

        print("\nColumn names:")
        print(df.columns.tolist())

        print("\nFirst 15 rows:")
        print(df.head(15).to_string(index=False))

        print("\nMissing values:")
        print(df.isnull().sum().to_string())

        print("\nData types:")
        print(df.dtypes.to_string())

        print("\nDuplicate rows:", df.duplicated().sum())

        # Identify likely date columns
        for col in df.columns:
            if "date" in col.lower():
                dates = pd.to_datetime(df[col], errors="coerce")
                if dates.notna().any():
                    print(
                        f"\nDate range in {col}:",
                        dates.min(),
                        "to",
                        dates.max()
                    )

    except Exception as e:
        print("ERROR:", str(e))

print("\n" + "=" * 65)
print("INSPECTION COMPLETED")
print("=" * 65)
