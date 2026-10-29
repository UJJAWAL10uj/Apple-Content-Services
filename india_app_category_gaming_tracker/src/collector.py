"""Collect dated India App Store chart snapshots from Apple's public RSS feeds."""
from __future__ import annotations

import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "categories.json"
RAW_PATH = ROOT / "data" / "raw" / "chart_snapshots.csv"
METADATA_PATH = ROOT / "data" / "processed" / "app_metadata.csv"
LOG_PATH = ROOT / "data" / "raw" / "collector.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler(LOG_PATH, encoding="utf-8")],
)
log = logging.getLogger(__name__)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "IndiaAppIntelligenceTracker/1.1 (research project)"})
TIMEOUT = 25

def get_json(url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    last_error = None
    for attempt in range(3):
        try:
            response = SESSION.get(url, params=params, timeout=TIMEOUT)
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            last_error = exc
            wait = 2 ** attempt
            log.warning("Request failed (attempt %s/3): %s | %s", attempt + 1, url, exc)
            time.sleep(wait)
    raise RuntimeError(f"Failed after 3 attempts: {url}: {last_error}")

def label(value: Any) -> Any:
    """Return an RSS label whether Apple encodes the value as a dict or scalar."""
    if isinstance(value, dict):
        return value.get("label")
    return value if isinstance(value, (str, int, float)) else None

def first_object(value: Any) -> dict[str, Any]:
    """Normalize RSS objects that may be a dict or a list of dicts."""
    if isinstance(value, dict):
        return value
    if isinstance(value, list):
        for item in value:
            if isinstance(item, dict):
                return item
    return {}

def parse_entry(entry: dict[str, Any], category: str, country: str,
                chart: str, rank: int, collected_at: str) -> dict[str, Any]:
    artist = first_object(entry.get("im:artist"))
    price = first_object(entry.get("im:price"))
    link = first_object(entry.get("link"))
    ident = first_object(entry.get("id"))
    attrs = first_object(ident.get("attributes"))
    app_id = attrs.get("im:id")
    if not app_id:
        raw_id = label(ident)
        # A feed ID may be a URL; preserve the numeric app ID if present.
        if raw_id:
            import re
            match = re.search(r"id(\d+)", str(raw_id))
            app_id = match.group(1) if match else raw_id
    return {
        "collected_at_utc": collected_at,
        "collection_date_utc": collected_at[:10],
        "country": country,
        "chart": chart,
        "category": category,
        "rank": rank,
        "app_id": str(app_id) if app_id is not None else None,
        "app_name": label(entry.get("im:name")),
        "developer": label(artist),
        "app_url": attrs.get("href") or first_object(link.get("attributes")).get("href"),
        "price_label": label(price),
        "feed_title": label(entry.get("title")),
        "feed_rights": label(entry.get("rights")),
    }

def fetch_chart(country: str, chart: str, limit: int, category: str,
                genre_id: int, collected_at: str) -> list[dict[str, Any]]:
    url = f"https://itunes.apple.com/{country}/rss/{chart}/limit={limit}/genre={genre_id}/json"
    payload = get_json(url)
    entries = payload.get("feed", {}).get("entry", [])
    if isinstance(entries, dict):
        entries = [entries]
    if not isinstance(entries, list):
        raise ValueError(f"Unexpected feed entry format for {category}: {type(entries).__name__}")
    rows = [
        parse_entry(e, category, country, chart, i, collected_at)
        for i, e in enumerate(entries, start=1) if isinstance(e, dict)
    ]
    if not rows:
        raise ValueError(f"No entries returned for {category}; feed URL: {url}")
    log.info("%s: received %d entries", category, len(rows))
    return rows

def lookup_metadata(app_ids: list[str], country: str) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    ids = [x for x in dict.fromkeys(app_ids) if x and str(x).isdigit()]
    for start in range(0, len(ids), 100):
        batch = ids[start:start + 100]
        try:
            payload = get_json(
                "https://itunes.apple.com/lookup",
                params={"id": ",".join(batch), "country": country},
            )
            for item in payload.get("results", []):
                output.append({
                    "looked_up_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "country": country,
                    "app_id": str(item.get("trackId", "")),
                    "bundle_id": item.get("bundleId"),
                    "app_name_lookup": item.get("trackName"),
                    "developer_lookup": item.get("artistName"),
                    "primary_genre": item.get("primaryGenreName"),
                    "genres": " | ".join(item.get("genres", []) or []),
                    "price": item.get("price"),
                    "currency": item.get("currency"),
                    "average_rating": item.get("averageUserRating"),
                    "rating_count": item.get("userRatingCount"),
                    "release_date": item.get("releaseDate"),
                    "current_version_release_date": item.get("currentVersionReleaseDate"),
                    "minimum_os_version": item.get("minimumOsVersion"),
                    "app_store_url": item.get("trackViewUrl"),
                    "description": item.get("description"),
                })
        except Exception as exc:
            log.warning("Metadata lookup batch failed (%d IDs): %s", len(batch), exc)
        time.sleep(1.0)
    return output

def append_unique_csv(new_df: pd.DataFrame, path: Path, key_cols: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.stat().st_size:
        old = pd.read_csv(path, dtype={"app_id": "string"})
        combined = pd.concat([old, new_df], ignore_index=True)
    else:
        combined = new_df
    if not combined.empty:
        combined = combined.drop_duplicates(subset=key_cols, keep="last")
    combined.to_csv(path, index=False, encoding="utf-8")

def main() -> None:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    country, chart, limit = config["country"], config["chart"], int(config["limit"])
    collected_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    observations: list[dict[str, Any]] = []
    category_errors = []

    for item in config["categories"]:
        try:
            observations.extend(fetch_chart(
                country, chart, limit, item["name"], int(item["genre_id"]), collected_at
            ))
        except Exception as exc:
            category_errors.append({"category": item["name"], "error": str(exc)})
            log.exception("Category collection failed: %s", item["name"])
        time.sleep(0.5)

    if not observations:
        raise SystemExit(
            "No chart observations were collected. Check internet access, Apple's feed, "
            "and config/categories.json. See data/raw/collector.log."
        )

    df = pd.DataFrame(observations)
    append_unique_csv(
        df, RAW_PATH,
        ["collected_at_utc", "country", "chart", "category", "rank", "app_id"],
    )
    log.info("Saved %d observations to %s", len(df), RAW_PATH)

    metadata = lookup_metadata(df["app_id"].dropna().astype(str).tolist(), country)
    if metadata:
        append_unique_csv(
            pd.DataFrame(metadata), METADATA_PATH,
            ["looked_up_at_utc", "country", "app_id"],
        )
        log.info("Saved %d metadata records to %s", len(metadata), METADATA_PATH)

    if category_errors:
        errors_path = ROOT / "data" / "raw" / "collection_errors.json"
        errors_path.write_text(json.dumps({
            "collected_at_utc": collected_at,
            "errors": category_errors,
        }, indent=2), encoding="utf-8")
        log.warning("%d categories had errors. Review %s", len(category_errors), errors_path)
    else:
        log.info("All configured categories returned entries.")
    log.info("Collection complete. Run: python -m src.analyze")

if __name__ == "__main__":
    main()
