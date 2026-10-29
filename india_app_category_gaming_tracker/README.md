# India App Category & Mobile Gaming Intelligence Tracker

A reproducible market-intelligence project that captures public India App Store chart snapshots, tracks app rank movement over time, and produces an Excel workbook, charts, and a weekly-style intelligence report.

> **Data integrity note:** this repository starts collecting observations when you run it. It does not contain fabricated historical chart data. The six-week analysis becomes meaningful after six weeks of daily snapshots. You can run it once immediately to verify setup.

## Research questions

1. Which apps persist in the top charts, and which show notable rank movement?
2. How do selected App Store categories differ in chart stability and turnover?
3. What broad product themes appear in chart descriptions and app metadata?
4. Which game subgenres and product formats are represented among charted apps?

## Data source and limitations

- **Chart source:** Apple's public RSS chart feeds, requested for the India storefront (`in`).
- **Metadata source:** Apple's public iTunes Lookup API, used to enrich app records where available.
- **Reference documentation:** [Apple iTunes Search API](https://performance-partners.apple.com/search-api), [Apple RSS marketing tools](https://rss.marketingtools.apple.com/).
- **Open-source reference:** [jparise/apprankings](https://github.com/jparise/apprankings), an older example of collecting App Store rankings into CSV. This project is an independent implementation, not a fork.

Public feeds can change, return fewer than 100 entries, or fail temporarily. The collector records the actual number returned and logs errors. Rankings are chart positions, not downloads, revenue, or market share. App metadata such as ratings can differ by storefront and can change between collection runs.

The iTunes Search API is a catalog search/lookup interface, not a historical ranking archive. This project therefore stores dated snapshots locally. It cannot backfill dates before collection unless a separately sourced, verifiable historical dataset is provided.

## Categories

The default category list is in `config/categories.json`. It includes Games, Social Networking, Entertainment, Photo & Video, Education, Health & Fitness, Finance, and Lifestyle. Feed support and returned entries should be validated during the first run.

## Quick start

Requires Python 3.10+.

```bash
# 1. Create and activate a virtual environment
python -m venv .venv

# Windows PowerShell
.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Collect today's chart snapshot
python -m src.collector

# 4. Build analysis outputs from all saved snapshots
python -m src.analyze
```

Run `python -m src.collector` once per day for six weeks. You can schedule it with Windows Task Scheduler, cron, or GitHub Actions after confirming that the first run works.

## Outputs

After collection and analysis:

- `data/raw/chart_snapshots.csv` — append-only chart observations.
- `data/processed/app_metadata.csv` — metadata returned by lookup calls.
- `data/processed/analysis_dataset.csv` — cleaned analytical dataset.
- `outputs/india_app_intelligence.xlsx` — Excel workbook with observations and summary sheets.
- `outputs/charts/` — category movement and rank distribution charts.
- `reports/latest_intelligence_report.md` — generated report based on the observations collected so far.

## Methodology

- One observation is one app in one chart/category on one collection date.
- Rank 1 is the highest chart position returned by the feed.
- Rank movement is calculated only when an app appears in both compared snapshots.
- An app missing from a later top chart is marked as `not_in_chart`, not assumed to have zero downloads or zero demand.
- Theme labels are keyword-based heuristics and should be manually reviewed before presenting insights as market conclusions.
- “Emerging” is operationally defined in the analysis as an app/theme with improving average rank or increasing representation across the observed snapshots. The report states the number of observed collection days.

## Suggested six-week operating plan

- **Day 1:** install, run collector, validate category feeds and workbook.
- **Days 2–7:** check data quality and refine theme keywords; do not change category definitions casually.
- **Weeks 2–5:** continue daily snapshots; review weekly changes.
- **Week 6:** run final analysis, validate the strongest findings against individual app records, and write a one-page executive summary.

## Resume integrity

Do not claim “25K chart entries,” “5 emerging themes,” or “3 format shifts” until the dataset and analysis actually support those numbers. The script reports observed row counts and findings so the final resume bullet can be updated from evidence.

## Repository structure

```text
india_app_category_gaming_tracker/
├── config/categories.json
├── data/raw/
├── data/processed/
├── outputs/charts/
├── reports/
├── src/collector.py
├── src/analyze.py
├── requirements.txt
└── README.md
```

## Next improvements

1. Add automated daily scheduling after feed validation.
2. Manually code a reviewed taxonomy for game subgenres and product themes.
3. Add a data-quality log and snapshot completeness checks.
4. Add a comparison with Google Play only if a permitted, documented data source is selected.
