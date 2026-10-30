# Festival & Cultural Seasonality Tracker

## Project Overview

A Python-based analytics project exploring cultural and event-driven
search-interest patterns in India and the Apple App Store landscape.

The project uses Google Trends data for eight search terms and
Apple App Store chart snapshots across six categories.

## Objectives

- Identify weekly search-interest peaks around cultural events.
- Analyze seasonal patterns in Google Trends data.
- Examine App Store category and developer representation.
- Build an interactive dashboard for exploring the findings.
- Identify potential opportunities for seasonal app experiences
  and content planning.

## Data Sources

### Google Trends
- Geography: India
- Period: 26 October 2025 to 25 October 2026
- Search terms: Diwali, Holi, Eid, Christmas, Onam, Pongal,
  Navratri and IPL
- Frequency: Weekly
- Observations: 424

### Apple App Store
- Categories: Games, Entertainment, Social Networking,
  Photo & Video, Shopping and Lifestyle
- Unique apps: 600
- Observations: 1,200
- Collection rounds: 2

## Technology Stack

- Python
- Pandas
- Streamlit
- Plotly
- CSV data processing
- Google Trends
- Apple App Store chart data

## Project Structure

festival_cultural_seasonality_tracker/
│
├── data/
│   ├── app_chart_snapshots.csv
│   ├── trends_diwali.csv
│   ├── trends_holi.csv
│   ├── trends_eid.csv
│   ├── trends_christmas.csv
│   ├── trends_onam.csv
│   ├── trends_pongal.csv
│   ├── trends_navratri.csv
│   └── trends_ipl.csv
│
├── reports/
│   ├── google_trends_cleaned.csv
│   ├── google_trends_keyword_summary.csv
│   ├── google_trends_monthly_patterns.csv
│   ├── final_festival_summary.csv
│   ├── festival_weekly_changes.csv
│   ├── final_app_category_summary.csv
│   └── final_developer_summary.csv
│
├── tracker.py
├── analyze_current_data.py
├── analyze_google_trends.py
├── final_analysis.py
├── app.py
└── requirements.txt

## How to Run

Install dependencies:

pip install -r requirements.txt

Generate Google Trends reports:

python analyze_google_trends.py

Generate final analysis:

python final_analysis.py

Launch dashboard:

streamlit run app.py

## Limitations

Google Trends scores are normalized relative-interest indices,
not absolute search volumes.

App Store rankings are ordinal positions and do not represent
downloads or revenue.

The two App Store collection rounds were approximately
13 minutes apart. Historical ranking seasonality cannot
be established from these snapshots.

The project is exploratory and does not establish causality
between festival search interest and App Store performance.