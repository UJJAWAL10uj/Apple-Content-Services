"""Analyze saved Apple App Store chart snapshots and export a workbook and report."""
from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone

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

# Specific terms first; avoid matching generic words such as "ai" inside
# unrelated words. App Store primary genres are used as a sensible fallback.
THEME_RULES = {
    "AI & productivity": [
        "artificial intelligence", "generative ai", " ai assistant", "ai chatbot",
        "chatbot", "productivity", "writing assistant", "note taking", "large language model",
    ],
    "Short video & creator tools": [
        "short video", "video editor", "reels", "creator tools", "video maker",
        "video editing", "photo editor", "streaming",
    ],
    "Casual & puzzle gaming": [
        "puzzle", "match-3", "match 3", "word game", "casual game",
        "brain game", "ludo", "solitaire", "mahjong",
    ],
    "Action & competitive gaming": [
        "battle royale", "multiplayer", "first person shooter", "fps game",
        "racing game", "shooter", "moba", "action game", "competitive gaming",
    ],
    "Finance & payments": [
        "payment", "upi", "wallet", "banking", "investment", "investing",
        "trading", "finance", "stock market", "personal finance",
    ],
    "Learning & language": [
        "learn", "language learning", "education", "online course", "quiz",
        "flashcard", "spoken english", "exam preparation", "learning app",
    ],
    "Health & fitness": [
        "fitness", "workout", "meditation", "health", "sleep tracker",
        "yoga", "running", "nutrition", "wellness",
    ],
    "Social & communication": [
        "social networking", "messaging", "chat app", "dating", "community",
        "video call", "voice call", "instant messaging",
    ],
}

GENRE_FALLBACKS = {
    "games": "Casual & puzzle gaming",
    "game": "Casual & puzzle gaming",
    "education": "Learning & language",
    "finance": "Finance & payments",
    "health & fitness": "Health & fitness",
    "medical": "Health & fitness",
    "social networking": "Social & communication",
    "photo & video": "Short video & creator tools",
    "entertainment": "Entertainment & streaming",
    "lifestyle": "Lifestyle & utilities",
    "utilities": "Lifestyle & utilities",
    "productivity": "AI & productivity",
    "business": "Business & work tools",
    "books": "Reading & reference",
    "reference": "Reading & reference",
    "news": "News & information",
    "travel": "Travel & navigation",
    "navigation": "Travel & navigation",
    "shopping": "Shopping & commerce",
    "food & drink": "Food & delivery",
    "music": "Music & audio",
    "sports": "Sports & recreation",
}

def classify_theme(app_name: str, primary_genre: str = "", genres: str = "",
                   description: str = "") -> str:
    """Assign a cautious theme using app text, then App Store genre fallback."""
    name = str(app_name or "").strip().lower()
    genre = str(primary_genre or "").strip().lower()
    genre_list = str(genres or "").strip().lower()
    desc = str(description or "").strip().lower()
    text = " ".join(part for part in (name, genre, genre_list, desc[:3000]) if part)

    # Strong app-name signals prevent unrelated description text from winning.
    name_rules = {
        "Facebook": ["facebook"],
        "Instagram": ["instagram"],
        "WhatsApp": ["whatsapp"],
        "Snapchat": ["snapchat"],
        "TikTok": ["tiktok"],
        "Netflix": ["netflix"],
        "JioHotstar": ["jiohotstar", "hotstar"],
        "YouTube": ["youtube"],
        "Google Pay": ["google pay", "gpay"],
        "PhonePe": ["phonepe"],
        "Paytm": ["paytm"],
        "Strava": ["strava"],
    }
    for app, terms in name_rules.items():
        if any(term in name for term in terms):
            if app in {"Facebook", "Instagram", "WhatsApp", "Snapchat", "TikTok"}:
                return "Social & communication"
            if app in {"Netflix", "JioHotstar", "YouTube"}:
                return "Entertainment & streaming" if app != "YouTube" else "Short video & creator tools"
            if app in {"Google Pay", "PhonePe", "Paytm"}:
                return "Finance & payments"
            if app == "Strava":
                return "Health & fitness"

    scores = {
        theme: sum(1 for term in terms if term in text)
        for theme, terms in THEME_RULES.items()
    }
    highest = max(scores.values(), default=0)
    winners = [theme for theme, score in scores.items() if score == highest and score > 0]

    # If keyword evidence is ambiguous, trust the primary App Store genre.
    if len(winners) == 1:
        return winners[0]
    if genre in GENRE_FALLBACKS:
        return GENRE_FALLBACKS[genre]
    for genre_name, theme in GENRE_FALLBACKS.items():
        if genre_name in genre_list:
            return theme
    return "Other / review"

def main() -> None:
    if not RAW_PATH.exists() or RAW_PATH.stat().st_size == 0:
        raise SystemExit("No chart snapshots found. Run `python -m src.collector` first.")

    df = pd.read_csv(RAW_PATH, dtype={"app_id": "string"})
    if df.empty:
        raise SystemExit("Chart snapshot file is empty.")

    required = {"collection_date_utc", "rank", "app_id", "country", "chart", "category", "app_name"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Snapshot file is missing required columns: {', '.join(sorted(missing))}")

    df["collection_date_utc"] = pd.to_datetime(df["collection_date_utc"], errors="coerce", utc=True)
    df["rank"] = pd.to_numeric(df["rank"], errors="coerce")
    df["app_id"] = df["app_id"].astype("string")
    df = df.dropna(subset=["collection_date_utc", "rank", "app_id"])
    df["app_key"] = df["country"].astype(str) + ":" + df["app_id"].astype(str)

    metadata_columns = [
        "primary_genre", "genres", "average_rating", "rating_count", "price", "currency",
        "release_date", "current_version_release_date", "app_store_url", "description",
    ]
    if METADATA_PATH.exists() and METADATA_PATH.stat().st_size:
        metadata = pd.read_csv(METADATA_PATH, dtype={"app_id": "string"})
        if {"country", "app_id"}.issubset(metadata.columns):
            metadata = metadata.drop_duplicates(["country", "app_id"], keep="last")
            keep = ["country", "app_id"] + [c for c in metadata_columns if c in metadata.columns]
            df = df.merge(metadata[keep], on=["country", "app_id"], how="left")
    for col in metadata_columns:
        if col not in df.columns:
            df[col] = pd.NA

    df["theme"] = df.apply(
        lambda row: classify_theme(
            row.get("app_name", ""), row.get("primary_genre", ""),
            row.get("genres", ""), row.get("description", "")
        ), axis=1
    )

    # A duplicate app/category/day should not create artificial rank movement.
    df = df.sort_values(
        ["country", "chart", "category", "app_key", "collection_date_utc", "rank"]
    )
    df = df.drop_duplicates(
        ["country", "chart", "category", "app_key", "collection_date_utc"], keep="first"
    )
    df["previous_rank"] = df.groupby(
        ["country", "chart", "category", "app_key"]
    )["rank"].shift(1)
    # Positive = improved; e.g. rank 20 -> rank 5 means +15.
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
    ).reset_index().sort_values("category")

    app_persistence = df.groupby(
        ["category", "app_key", "app_name", "developer"], dropna=False
    ).agg(
        observed_snapshots=("collection_date_utc", "nunique"),
        best_rank=("rank", "min"),
        average_rank=("rank", "mean"),
        latest_observed_date=("collection_date_utc", "max"),
        theme=("theme", "last"),
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

    # Keep only each app's most recent observed rank transition, then rank by movement.
    rank_changes = df.dropna(subset=["previous_rank"]).copy()
    if not rank_changes.empty:
        movers = rank_changes.sort_values("collection_date_utc").groupby(
            ["country", "chart", "category", "app_key"], as_index=False
        ).tail(1)
        movers = movers.sort_values("rank_improvement", ascending=False)
    else:
        movers = rank_changes

    CHART_DIR.mkdir(parents=True, exist_ok=True)
    counts = df.groupby("category")["app_key"].count().sort_values()
    plt.figure(figsize=(10, 5))
    counts.plot(kind="barh")
    plt.title("Collected chart observations by category")
    plt.xlabel("Observation rows")
    plt.ylabel("Category")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "observations_by_category.png", dpi=160)
    plt.close()

    plt.figure(figsize=(12, 5))
    latest.boxplot(column="rank", by="category", rot=35)
    plt.suptitle("")
    plt.title("Rank distribution in latest observed snapshot")
    plt.xlabel("Category")
    plt.ylabel("Chart rank (lower is better)")
    plt.tight_layout()
    plt.savefig(CHART_DIR / "latest_rank_distribution.png", dpi=160)
    plt.close()

    theme_counts = latest.groupby(["category", "theme"]).size().unstack(fill_value=0)
    if not theme_counts.empty:
        ax = theme_counts.plot(kind="bar", stacked=True, figsize=(12, 6))
        ax.set_title("Theme composition by App Store category (latest snapshot)")
        ax.set_xlabel("Category")
        ax.set_ylabel("Apps")
        ax.legend(title="Theme", bbox_to_anchor=(1.02, 1), loc="upper left")
        plt.tight_layout()
        plt.savefig(CHART_DIR / "theme_composition_by_category.png", dpi=160)
        plt.close()

    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(PROCESSED_PATH, index=False, encoding="utf-8")
    WORKBOOK_PATH.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(WORKBOOK_PATH, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="Observations", index=False)
        category_summary.to_excel(writer, sheet_name="Category Summary", index=False)
        app_persistence.to_excel(writer, sheet_name="App Persistence", index=False)
        theme_summary.to_excel(writer, sheet_name="Theme Summary", index=False)
        movers.head(100).to_excel(writer, sheet_name="Rank Movers", index=False)
        for ws in writer.book.worksheets:
            ws.freeze_panes = "A2"
            ws.auto_filter.ref = ws.dimensions
            for column_cells in ws.columns:
                max_len = min(max(len(str(c.value or "")) for c in column_cells) + 2, 45)
                ws.column_dimensions[column_cells[0].column_letter].width = max(12, max_len)

    report_lines = [
        "# India App Category & Mobile Gaming Intelligence", "",
        f"**Generated (UTC):** {datetime.now(timezone.utc).isoformat(timespec='seconds')}",
        f"**Observed collection dates:** {days_observed}",
        f"**First date in dataset:** {first_date.date()}",
        f"**Latest date in dataset:** {latest_date.date()}",
        f"**Total observation rows:** {len(df):,}",
        f"**Unique app IDs:** {df['app_key'].nunique():,}", "",
        "## Executive readout", "",
        ("This is an initial collection check. Treat theme labels as provisional and avoid trend "
         "claims until multiple dates have accumulated." if days_observed < 7 else
         "Interpret results in the context of the observed date range; rank is not market share."),
        "", "## Latest snapshot by category", "",
        category_summary.to_markdown(index=False, floatfmt=".2f"), "",
        "## Most persistent apps", "",
        app_persistence.sort_values(
            ["observed_snapshots", "best_rank"], ascending=[False, True]
        ).head(15).to_markdown(index=False, floatfmt=".2f"), "",
        "## Themes in latest snapshot", "",
        theme_summary.to_markdown(index=False, floatfmt=".2f"), "",
        "## Largest observed rank improvements", "",
        (movers[["category", "app_name", "developer", "previous_rank", "rank",
                 "rank_improvement", "collection_date_utc"]].head(15).to_markdown(index=False)
         if not movers.empty else "Not enough repeated observations yet to calculate rank movement."),
        "", "## Interpretation cautions", "",
        "- Rank is relative chart position, not downloads, revenue, or market share.",
        "- Apps absent from a chart are not assigned a zero rank.",
        "- Theme labels use keyword rules and genre fallbacks; ambiguous cases need human review.",
        "- The report uses only dates present in the local dataset; it does not invent historical observations.",
        "- A one-day dataset cannot support claims about sustained trends or seasonality.", "",
        "## Suggested analyst follow-up", "",
        "1. Review `Other / review` and a sample of automatically assigned themes.",
        "2. Collect snapshots daily without overwriting earlier dates.",
        "3. Check rank movements only for apps with repeated observations.",
        "4. Make trend claims only after enough observations exist to support them.",
    ]
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(f"Analysis complete. Observations: {len(df):,}; unique dates: {days_observed}")
    print(f"Workbook: {WORKBOOK_PATH}")
    print(f"Report: {REPORT_PATH}")
    print(f"Charts: {CHART_DIR}")

if __name__ == "__main__":
    main()
