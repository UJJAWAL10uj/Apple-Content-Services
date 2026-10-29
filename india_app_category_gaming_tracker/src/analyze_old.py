"""Analyze saved chart snapshots and export an Excel workbook and report."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import re

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "raw" / "chart_snapshots.csv"
METADATA_PATH = ROOT / "data" / "processed" / "app_metadata.csv"
PROCESSED_PATH = ROOT / "data" / "processed" / "analysis_dataset.csv"
WORKBOOK_PATH = ROOT / "outputs" / "india_app_intelligence.xlsx"
CHART_DIR = ROOT / "outputs" / "charts"
REPORT_PATH = ROOT / "reports" / "latest_intelligence_report.md"

THEME_RULES = {
    "AI & productivity": ["artificial intelligence", " ai ", "assistant", "chatbot", "productivity", "writing"],
    "Short video & creator tools": ["short video", "video editor", "reels", "creator", "video maker", "streaming"],
    "Casual & puzzle gaming": ["puzzle", "match-3", "match 3", "word game", "casual", "brain game"],
    "Action & competitive gaming": ["battle royale", "multiplayer", "fps", "racing", "shooter", "moba"],
    "Finance & payments": ["payment", "upi", "wallet", "banking", "invest", "trading", "finance"],
    "Learning & language": ["learn", "language", "education", "course", "quiz", "flashcard"],
    "Health & fitness": ["fitness", "workout", "meditation", "health", "sleep", "yoga"],
    "Social & communication": ["social", "chat", "messaging", "dating", "community"],
}

def classify_theme(text: str) -> str:
    normalized = f" {str(text or '').lower()} "
    scores = {
        theme: sum(1 for term in terms if term in normalized)
        for theme, terms in THEME_RULES.items()
    }
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "Other / review"

def main() -> None:
    if not RAW_PATH.exists() or RAW_PATH.stat().st_size == 0:
        raise SystemExit("No chart snapshots found. Run `python -m src.collector` first.")

    df = pd.read_csv(RAW_PATH, dtype={"app_id": "string"})
    if df.empty:
        raise SystemExit("Chart snapshot file is empty.")

    df["collection_date_utc"] = pd.to_datetime(df["collection_date_utc"], errors="coerce")
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df["app_id"] = df["app_id"].astype("string")
    df = df.dropna(subset=["collection_date_utc", "rank", "app_id"])
    df["app_key"] = df["country"].astype(str) + ":" + df["app_id"].astype(str)

    metadata = pd.DataFrame()
    if METADATA_PATH.exists() and METADATA_PATH.stat().st_size:
        metadata = pd.read_csv(METADATA_PATH, dtype={"app_id": "string"})
        metadata = metadata.drop_duplicates(["country", "app_id"], keep="last")
        df = df.merge(
            metadata[["country", "app_id", "primary_genre", "genres", "average_rating",
                      "rating_count", "price", "currency", "release_date",
                      "current_version_release_date", "app_store_url", "description"]],
            on=["country", "app_id"], how="left"
        )
    else:
        for col in ["primary_genre", "genres", "average_rating", "rating_count", "price",
                    "currency", "release_date", "current_version_release_date",
                    "app_store_url", "description"]:
            df[col] = pd.NA

    df["theme"] = (
        df["app_name"].fillna("").astype(str) + " " +
        df["primary_genre"].fillna("").astype(str) + " " +
        df["genres"].fillna("").astype(str) + " " +
        df["description"].fillna("").astype(str).str.slice(0, 3000)
    ).map(classify_theme)

    df = df.sort_values(["country", "chart", "category", "app_key", "collection_date_utc", "rank"])
    df["previous_rank"] = df.groupby(
        ["country", "chart", "category", "app_key"]
    )["rank"].shift(1)
    # Positive means improved (e.g. rank 20 -> rank 5 = +15).
    df["rank_improvement"] = df["previous_rank"] - df["rank"]

    latest_date = df["collection_date_utc"].max()
    latest = df[df["collection_date_utc"] == latest_date].copy()
    first_date = df["collection_date_utc"].min()
    days_observed = df["collection_date_utc"].dt.date.nunique()

    category_summary = latest.groupby("category", dropna=False).agg(
        apps_in_latest_snapshot=("app_key", "nunique"),
        average_rank=("rank", "mean"),
        median_rank=("rank", "median"),
        top_10_apps=("rank", lambda s: int((s <= 10).sum())),
    ).reset_index().sort_values("average_rank")

    app_persistence = df.groupby(
        ["category", "app_key", "app_name", "developer"], dropna=False
    ).agg(
        observed_snapshots=("collection_date_utc", "nunique"),
        best_rank=("rank", "min"),
        average_rank=("rank", "mean"),
        latest_observed_date=("collection_date_utc", "max"),
        theme=("theme", lambda s: s.dropna().iloc[-1] if len(s.dropna()) else "Other / review"),
    ).reset_index()
    app_persistence["share_of_observed_days"] = (
        app_persistence["observed_snapshots"] / max(days_observed, 1)
    )
    app_persistence = app_persistence.sort_values(
        ["category", "observed_snapshots", "best_rank"], ascending=[True, False, True]
    )

    theme_summary = latest.groupby(["category", "theme"], dropna=False).agg(
        apps=("app_key", "nunique"),
        average_rank=("rank", "mean"),
    ).reset_index().sort_values(["category", "apps"], ascending=[True, False])

    rank_changes = df.dropna(subset=["previous_rank"]).copy()
    if not rank_changes.empty:
        movers = rank_changes.sort_values("rank_improvement", ascending=False).groupby(
            ["category", "app_key"], as_index=False
        ).tail(1).sort_values("rank_improvement", ascending=False)
    else:
        movers = rank_changes

    CHART_DIR.mkdir(parents=True, exist_ok=True)
    # Chart 1: count of observations per category across collected snapshots.
    counts = df.groupby("category")["app_key"].count().sort_values()
    plt.figure(figsize=(10, 5))
    counts.plot(kind="barh")
    plt.title("Collected chart observations by category")
    plt.xlabel("Observation rows")
    plt.ylabel("Category")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "observations_by_category.png", dpi=160)
    plt.close()

    # Chart 2: latest snapshot rank distribution.
    plt.figure(figsize=(10, 5))
    latest.boxplot(column="rank", by="category", rot=35)
    plt.suptitle("")
    plt.title("Rank distribution in latest observed snapshot")
    plt.xlabel("Category")
    plt.ylabel("Chart rank (lower is better)")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "latest_rank_distribution.png", dpi=160)
    plt.close()

    df.to_csv(PROCESSED_PATH, index=False, encoding="utf-8")
    WORKBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(WORKBOOK_PATH, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Observations", index=False)
        category_summary.to_excel(writer, sheet_name="Category Summary", index=False)
        app_persistence.to_excel(writer, sheet_name="App Persistence", index=False)
        theme_summary.to_excel(writer, sheet_name="Theme Summary", index=False)
        movers.head(100).to_excel(writer, sheet_name="Rank Movers", index=False)
        # Freeze headers and enable filters for usability.
        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for column_cells in ws.columns:
                max_len = min(max(len(str(c.value or "")) for c in column_cells) + 2, 45)
                ws.column_dimensions[column_cells[0].column_letter].width = max(12, max_len)

    report_lines = [
        "# India App Category & Mobile Gaming Intelligence",
        "",
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"**Observed collection dates:** {days_observed}",
        f"**First date in dataset:** {first_date.date()}",
        f"**Latest date in dataset:** {latest_date.date()}",
        f"**Total observation rows:** {len(df):,}",
        f"**Unique app IDs:** {df['app_key'].nunique():,}",
        "",
        "## Executive readout",
        "",
        "This report is generated from the snapshots currently present in the local dataset. "
        "Treat early results as a collection check until multiple dates have accumulated.",
        "",
        "## Latest snapshot by category",
        "",
        category_summary.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Most persistent apps",
        "",
        app_persistence.sort_values(
            ["observed_snapshots", "best_rank"], ascending=[False, True]
        ).head(15).to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Themes in latest snapshot",
        "",
        theme_summary.to_markdown(index=False, floatfmt=".2f"),
        "",
        "## Largest observed rank improvements",
        "",
        (movers[["category", "app_name", "developer", "previous_rank", "rank",
                 "rank_improvement", "collection_date_utc"]].head(15).to_markdown(index=False)
         if not movers.empty else "Not enough repeated observations yet to calculate rank movement."),
        "",
        "## Interpretation cautions",
        "",
        "- Rank is relative chart position, not downloads, revenue, or market share.",
        "- Apps absent from a chart are not assigned a zero rank.",
        "- Keyword-based theme labels are provisional and need human review.",
        "- The number of unique collection dates is reported explicitly; this dataset does not invent prior observations.",
        "- A one-day dataset cannot support claims about sustained trends or seasonality.",
        "",
        "## Suggested analyst follow-up",
        "",
        "1. Review the top rank movers and confirm the same app is matched by app ID.",
        "2. Manually inspect theme labels, especially `Other / review` and any ambiguous games.",
        "3. Compare weekly snapshots only after at least two complete weeks exist.",
        "4. Write conclusions as hypotheses unless supported by repeated observations.",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Analysis complete. Observations: {len(df):,}; unique dates: {days_observed}")
    print(f"Workbook: {WORKBOOK_PATH}")
    print(f"Report: {REPORT_PATH}")
    print(f"Charts: {CHART_DIR}")

if __name__ == "__main__":
    main()
