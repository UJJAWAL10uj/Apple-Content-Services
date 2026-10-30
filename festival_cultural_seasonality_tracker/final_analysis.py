
import pandas as pd
from pathlib import Path

DATA = Path("data")
REPORTS = Path("reports")
REPORTS.mkdir(exist_ok=True)

# Load Google Trends data
trends = pd.read_csv(REPORTS / "google_trends_cleaned.csv")
trends["date"] = pd.to_datetime(trends["date"])
trends["interest"] = pd.to_numeric(trends["interest"], errors="coerce")

# Festival/event search summary
festival_summary = (
    trends.groupby("keyword")
    .agg(
        weeks_observed=("interest", "count"),
        average_interest=("interest", "mean"),
        peak_interest=("interest", "max"),
        lowest_interest=("interest", "min")
    )
    .reset_index()
)

peak_rows = trends.loc[
    trends.groupby("keyword")["interest"].idxmax(),
    ["keyword", "date", "interest"]
].rename(columns={"date": "peak_date"})

festival_summary = festival_summary.merge(
    peak_rows[["keyword", "peak_date"]],
    on="keyword"
)

festival_summary["average_interest"] = (
    festival_summary["average_interest"].round(2)
)

festival_summary.to_csv(
    REPORTS / "final_festival_summary.csv", index=False
)

# Calculate the change in interest from the previous week.
trends = trends.sort_values(["keyword", "date"])
trends["previous_interest"] = (
    trends.groupby("keyword")["interest"].shift(1)
)
trends["weekly_change"] = (
    trends["interest"] - trends["previous_interest"]
)

trends.to_csv(
    REPORTS / "festival_weekly_changes.csv", index=False
)

# Load App Store data
apps = pd.read_csv(DATA / "app_chart_snapshots.csv")
apps["rank"] = pd.to_numeric(apps["rank"], errors="coerce")

# Category landscape
category_summary = (
    apps.groupby("category")
    .agg(
        total_observations=("app_id", "count"),
        unique_apps=("app_id", "nunique"),
        unique_developers=("developer", "nunique"),
        average_rank=("rank", "mean"),
        best_rank=("rank", "min")
    )
    .reset_index()
)

category_summary["average_rank"] = (
    category_summary["average_rank"].round(2)
)

category_summary.to_csv(
    REPORTS / "final_app_category_summary.csv", index=False
)

# Developer landscape
developer_summary = (
    apps.groupby("developer")
    .agg(
        unique_apps=("app_id", "nunique"),
        categories_present=("category", "nunique")
    )
    .reset_index()
    .sort_values("unique_apps", ascending=False)
)

developer_summary.to_csv(
    REPORTS / "final_developer_summary.csv", index=False
)

# Collection period and quality checks
apps["collected_at_utc"] = pd.to_datetime(
    apps["collected_at_utc"], errors="coerce", utc=True
)

collection_summary = pd.DataFrame([{
    "app_store_observations": len(apps),
    "unique_apps": apps["app_id"].nunique(),
    "categories": apps["category"].nunique(),
    "snapshot_timestamps": apps["collected_at_utc"].nunique(),
    "google_trends_observations": len(trends),
    "google_trends_keywords": trends["keyword"].nunique(),
    "trends_missing_values": int(trends["interest"].isna().sum())
}])

collection_summary.to_csv(
    REPORTS / "final_project_data_summary.csv", index=False
)

print("\n========== FESTIVAL / EVENT SEARCH SUMMARY ==========")
print(festival_summary.to_string(index=False))

print("\n========== APP STORE CATEGORY SUMMARY ==========")
print(category_summary.to_string(index=False))

print("\n========== TOP DEVELOPERS ==========")
print(developer_summary.head(10).to_string(index=False))

print("\n========== PROJECT DATA SUMMARY ==========")
print(collection_summary.to_string(index=False))

print("\nCreated final reports:")
for file in [
    "final_festival_summary.csv",
    "festival_weekly_changes.csv",
    "final_app_category_summary.csv",
    "final_developer_summary.csv",
    "final_project_data_summary.csv"
]:
    print("reports/" + file)

print("\nFINAL ANALYSIS COMPLETE")
