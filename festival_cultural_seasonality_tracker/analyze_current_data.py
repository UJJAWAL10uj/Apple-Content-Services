
import pandas as pd
from pathlib import Path

# -----------------------------------------
# 1. PATHS
# -----------------------------------------

DATA_FILE = Path("data/app_chart_snapshots.csv")
OUTPUT_DIR = Path("reports")
OUTPUT_DIR.mkdir(exist_ok=True)

if not DATA_FILE.exists():
    raise FileNotFoundError(f"Dataset not found: {DATA_FILE}")

# -----------------------------------------
# 2. LOAD AND CLEAN DATA
# -----------------------------------------

df = pd.read_csv(DATA_FILE)

df["snapshot_date"] = pd.to_datetime(
    df["snapshot_date"], errors="coerce"
)

df["collected_at_utc"] = pd.to_datetime(
    df["collected_at_utc"], errors="coerce", utc=True
)

df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
df["app_id"] = df["app_id"].astype("string")

df = df.dropna(
    subset=["collected_at_utc", "category", "app_id", "rank"]
)

df = df.sort_values(
    ["category", "collected_at_utc", "rank"]
).reset_index(drop=True)

print("\n===================================")
print("FESTIVAL SEASONALITY TRACKER")
print("INITIAL ANALYTICS ENGINE")
print("===================================")

# -----------------------------------------
# 3. BASIC DATA QUALITY
# -----------------------------------------

print("\n1. DATA QUALITY")

print("Total records:", len(df))
print("Unique apps:", df["app_id"].nunique())
print("Categories:", df["category"].nunique())
print("Collection timestamps:",
      df["collected_at_utc"].nunique())

print("\nMissing values:")
print(df.isna().sum().to_string())

# Exact duplicate observations within a collection
duplicate_mask = df.duplicated(
    subset=[
        "collected_at_utc",
        "category",
        "app_id"
    ],
    keep=False
)

duplicates = df[duplicate_mask].copy()

duplicates.to_csv(
    OUTPUT_DIR / "duplicate_observations.csv",
    index=False
)

print("\nDuplicate observations:", len(duplicates))

# -----------------------------------------
# 4. COLLECTION SUMMARY
# -----------------------------------------

print("\n2. COLLECTION SUMMARY")

collection_summary = (
    df.groupby(["category", "collected_at_utc"])
    .agg(
        total_apps=("app_id", "size"),
        unique_apps=("app_id", "nunique"),
        best_rank=("rank", "min"),
        worst_rank=("rank", "max")
    )
    .reset_index()
)

collection_summary.to_csv(
    OUTPUT_DIR / "collection_summary.csv",
    index=False
)

print(collection_summary.to_string(index=False))

# -----------------------------------------
# 5. CATEGORY-LEVEL SNAPSHOT COMPARISON
# -----------------------------------------

print("\n3. CATEGORY RANKING COMPARISON")

comparison_results = []

for category, group in df.groupby("category"):

    timestamps = sorted(
        group["collected_at_utc"].dropna().unique()
    )

    if len(timestamps) < 2:
        print(f"{category}: Need at least 2 snapshots")
        continue

    first_time = timestamps[0]
    last_time = timestamps[-1]

    first = group[
        group["collected_at_utc"] == first_time
    ][["app_id", "app_name", "rank"]].copy()

    last = group[
        group["collected_at_utc"] == last_time
    ][["app_id", "app_name", "rank"]].copy()

    first = first.drop_duplicates("app_id")
    last = last.drop_duplicates("app_id")

    merged = first.merge(
        last,
        on="app_id",
        how="outer",
        suffixes=("_first", "_last"),
        indicator=True
    )

    common = merged[merged["_merge"] == "both"].copy()

    # Positive value means ranking improved.
    common["rank_improvement"] = (
        common["rank_first"] - common["rank_last"]
    )

    common["category"] = category

    common["movement"] = common[
        "rank_improvement"
    ].apply(
        lambda x: (
            "Improved" if x > 0
            else "Declined" if x < 0
            else "Unchanged"
        )
    )

    improved = int(
        (common["rank_improvement"] > 0).sum()
    )

    declined = int(
        (common["rank_improvement"] < 0).sum()
    )

    unchanged = int(
        (common["rank_improvement"] == 0).sum()
    )

    new_apps = int(
        (merged["_merge"] == "right_only").sum()
    )

    exited_apps = int(
        (merged["_merge"] == "left_only").sum()
    )

    comparison_results.append({
        "category": category,
        "first_snapshot": str(first_time),
        "last_snapshot": str(last_time),
        "first_apps": len(first),
        "last_apps": len(last),
        "common_apps": len(common),
        "improved": improved,
        "declined": declined,
        "unchanged": unchanged,
        "new_entries": new_apps,
        "exited_apps": exited_apps,
        "average_rank_improvement":
            round(common["rank_improvement"].mean(), 2)
            if len(common) else None
    })

    common.to_csv(
        OUTPUT_DIR / f"{category.lower().replace(' ', '_')}_rank_comparison.csv",
        index=False
    )

    print(f"\n{category}")
    print("Common apps:", len(common))
    print("Improved:", improved)
    print("Declined:", declined)
    print("Unchanged:", unchanged)
    print("New entries:", new_apps)
    print("Exited apps:", exited_apps)

# -----------------------------------------
# 6. EXPORT FINAL COMPARISON
# -----------------------------------------

comparison_df = pd.DataFrame(comparison_results)

comparison_df.to_csv(
    OUTPUT_DIR / "category_rank_comparison.csv",
    index=False
)

print("\n4. FINAL CATEGORY COMPARISON")

if not comparison_df.empty:
    print(comparison_df.to_string(index=False))

# -----------------------------------------
# 7. DEVELOPER ANALYSIS
# -----------------------------------------

print("\n5. TOP DEVELOPERS")

developer_summary = (
    df.groupby("developer")
    .agg(
        app_count=("app_id", "nunique"),
        average_rank=("rank", "mean"),
        categories=("category", "nunique")
    )
    .reset_index()
    .sort_values(
        ["app_count", "average_rank"],
        ascending=[False, True]
    )
)

developer_summary.to_csv(
    OUTPUT_DIR / "developer_analysis.csv",
    index=False
)

print(developer_summary.head(15).to_string(index=False))

# -----------------------------------------
# 8. CATEGORY APP CONCENTRATION
# -----------------------------------------

print("\n6. CATEGORY CONCENTRATION")

category_summary = (
    df.groupby("category")
    .agg(
        total_records=("app_id", "size"),
        unique_apps=("app_id", "nunique"),
        unique_developers=("developer", "nunique"),
        average_rank=("rank", "mean")
    )
    .reset_index()
)

category_summary.to_csv(
    OUTPUT_DIR / "category_analysis.csv",
    index=False
)

print(category_summary.to_string(index=False))

# -----------------------------------------
# 9. COMPLETION
# -----------------------------------------

print("\n===================================")
print("ANALYSIS COMPLETED")
print("===================================")

print("\nFiles generated in reports/:")

for file in sorted(OUTPUT_DIR.glob("*.csv")):
    print("-", file.name)

print("\nNext: Validate festival calendar and import trends.")
