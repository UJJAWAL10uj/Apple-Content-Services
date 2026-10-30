
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data")
REPORT_DIR = Path("reports")
REPORT_DIR.mkdir(exist_ok=True)

FILES = {
    "Diwali": "trends_diwali.csv",
    "Holi": "trends_holi.csv",
    "Eid": "trends_eid.csv",
    "Christmas": "trends_christmas.csv",
    "Onam": "trends_onam.csv",
    "Pongal": "trends_pongal.csv",
    "Navratri": "trends_navratri.csv",
    "IPL": "trends_ipl.csv",
}

def load_trends_file(keyword, filename):
    path = DATA_DIR / filename

    if not path.exists():
        print(f"WARNING: Missing file: {filename}")
        return None

    # Read the Google Trends CSV.
    df = pd.read_csv(path)

    # Clean column names.
    df.columns = [str(c).strip() for c in df.columns]

    # Google Trends format: Time | Festival name
    date_column = next(
        (c for c in df.columns if c.lower() in ["time", "week", "day", "date"]),
        None
    )

    if date_column is None:
        print(f"WARNING: No date column in {filename}")
        print("Columns found:", df.columns.tolist())
        return None

    value_columns = [c for c in df.columns if c != date_column]

    if not value_columns:
        print(f"WARNING: No interest column in {filename}")
        return None

    interest_column = value_columns[0]

    df = df.rename(columns={
        date_column: "date",
        interest_column: "interest"
    })

    # Your example uses dates like 26-10-2025.
    df["date"] = pd.to_datetime(
    df["date"],
    format="%Y-%m-%d",
    errors="coerce"
    )

    # Handle Google Trends values such as <1.
    df["interest"] = (
        df["interest"]
        .astype(str)
        .str.strip()
        .str.replace("<1", "0.5", regex=False)
        .str.replace(",", "", regex=False)
    )

    df["interest"] = pd.to_numeric(
        df["interest"],
        errors="coerce"
    )

    df = df.dropna(subset=["date", "interest"])

    df["keyword"] = keyword
    df["geo"] = "India"
    df["source"] = "Google Trends"

    return df[["date", "keyword", "geo", "interest", "source"]]


all_data = []

print("\n========== LOADING GOOGLE TRENDS FILES ==========")

for keyword, filename in FILES.items():
    df = load_trends_file(keyword, filename)

    if df is not None and not df.empty:
        all_data.append(df)
        print(
            f"{keyword}: {len(df)} observations | "
            f"{df['date'].min().date()} to {df['date'].max().date()}"
        )

if not all_data:
    raise SystemExit("No data loaded. Check the CSV files.")

trends = pd.concat(all_data, ignore_index=True)

trends = trends.drop_duplicates(
    subset=["date", "keyword"]
)

trends = trends.sort_values(
    ["keyword", "date"]
).reset_index(drop=True)

# 1. Combined dataset
trends.to_csv(
    REPORT_DIR / "google_trends_cleaned.csv",
    index=False
)

# 2. Keyword summary
summary = (
    trends.groupby("keyword")
    .agg(
        observations=("interest", "count"),
        average_interest=("interest", "mean"),
        maximum_interest=("interest", "max"),
        minimum_interest=("interest", "min")
    )
    .reset_index()
)

peak_dates = (
    trends.loc[
        trends.groupby("keyword")["interest"].idxmax(),
        ["keyword", "date"]
    ]
    .rename(columns={"date": "peak_date"})
)

summary = summary.merge(peak_dates, on="keyword", how="left")

summary["average_interest"] = summary["average_interest"].round(2)

summary = summary.sort_values(
    "maximum_interest",
    ascending=False
)

summary.to_csv(
    REPORT_DIR / "google_trends_keyword_summary.csv",
    index=False
)

# 3. Monthly patterns
trends["month"] = trends["date"].dt.month_name()

monthly = (
    trends.groupby(["keyword", "month"], as_index=False)
    .agg(
        average_interest=("interest", "mean"),
        peak_interest=("interest", "max"),
        observations=("interest", "count")
    )
)

monthly["average_interest"] = monthly["average_interest"].round(2)

monthly.to_csv(
    REPORT_DIR / "google_trends_monthly_patterns.csv",
    index=False
)

print("\n========== KEYWORD SUMMARY ==========")
print(summary.to_string(index=False))

print("\n========== DATA QUALITY ==========")
print("Total observations:", len(trends))
print("Unique keywords:", trends["keyword"].nunique())
print("Missing values:")
print(trends.isna().sum().to_string())

print("\n========== FILES CREATED ==========")
print("reports/google_trends_cleaned.csv")
print("reports/google_trends_keyword_summary.csv")
print("reports/google_trends_monthly_patterns.csv")

print("\nGOOGLE TRENDS ANALYSIS COMPLETE")
