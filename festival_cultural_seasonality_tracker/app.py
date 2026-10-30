
import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

REPORTS = Path("reports")
DATA = Path("data")

st.set_page_config(
    page_title="Festival & Cultural Seasonality Tracker",
    page_icon="📊",
    layout="wide"
)

st.title("Festival & Cultural Seasonality Tracker")
st.caption(
    "India | Google Trends interest and Apple App Store category landscape"
)

# Load datasets
@st.cache_data
def load_data():
    trends = pd.read_csv(REPORTS / "google_trends_cleaned.csv")
    trends["date"] = pd.to_datetime(trends["date"])

    apps = pd.read_csv(DATA / "app_chart_snapshots.csv")
    apps["rank"] = pd.to_numeric(apps["rank"], errors="coerce")

    festival = pd.read_csv(REPORTS / "final_festival_summary.csv")
    category = pd.read_csv(REPORTS / "final_app_category_summary.csv")
    developers = pd.read_csv(REPORTS / "final_developer_summary.csv")

    return trends, apps, festival, category, developers

try:
    trends, apps, festival, category, developers = load_data()
except Exception as error:
    st.error(f"Could not load project data: {error}")
    st.info(
        "Run python analyze_google_trends.py and "
        "python final_analysis.py before starting the dashboard."
    )
    st.stop()

# Sidebar filters
st.sidebar.header("Dashboard filters")

keywords = sorted(trends["keyword"].dropna().unique())
selected_keywords = st.sidebar.multiselect(
    "Choose festivals/events",
    keywords,
    default=keywords
)

categories = sorted(apps["category"].dropna().unique())
selected_categories = st.sidebar.multiselect(
    "Choose App Store categories",
    categories,
    default=categories
)

filtered_trends = trends[
    trends["keyword"].isin(selected_keywords)
].copy()

filtered_apps = apps[
    apps["category"].isin(selected_categories)
].copy()

# KPI metrics
c1, c2, c3, c4 = st.columns(4)

c1.metric("Search observations", f"{len(trends):,}")
c2.metric("Search terms", trends["keyword"].nunique())
c3.metric("Unique apps", f"{apps['app_id'].nunique():,}")
c4.metric("App categories", apps["category"].nunique())

st.divider()

# Section 1: Search trends
st.header("1. Festival and event search interest")

st.write(
    "Google Trends reports relative search interest on a normalized "
    "0–100 scale for each search term. Compare the shape and timing "
    "of each term's trend, not its absolute search volume against "
    "another term."
)

if not filtered_trends.empty:
    fig = px.line(
        filtered_trends,
        x="date",
        y="interest",
        color="keyword",
        markers=True,
        title="Weekly Google Trends interest",
        labels={
            "date": "Week",
            "interest": "Relative search interest",
            "keyword": "Search term"
        }
    )
    fig.update_layout(hovermode="x unified")
    st.plotly_chart(fig, width='stretch')

    st.subheader("Search-interest peak summary")
    selected_summary = festival[
        festival["keyword"].isin(selected_keywords)
    ].sort_values("peak_interest", ascending=False)

    st.dataframe(selected_summary, width='stretch')

    st.download_button(
        "Download festival summary CSV",
        selected_summary.to_csv(index=False),
        file_name="festival_summary.csv",
        mime="text/csv"
    )
else:
    st.warning("Select at least one search term.")

st.divider()

# Section 2: App Store landscape
st.header("2. Apple App Store landscape")

st.write(
    "This section describes the collected chart rankings, app coverage "
    "and developer presence. Rank 1 is the highest chart position."
)

if not filtered_apps.empty:
    category_view = (
        filtered_apps.groupby("category", as_index=False)
        .agg(
            unique_apps=("app_id", "nunique"),
            average_rank=("rank", "mean"),
            best_rank=("rank", "min")
        )
    )

    fig = px.bar(
        category_view,
        x="category",
        y="unique_apps",
        title="Unique apps collected by category",
        labels={
            "category": "App Store category",
            "unique_apps": "Unique apps"
        },
        text="unique_apps"
    )
    st.plotly_chart(fig, width='stretch')

    fig = px.bar(
        category_view,
        x="category",
        y="average_rank",
        title="Average chart rank by category",
        labels={
            "category": "App Store category",
            "average_rank": "Average rank (lower is better)"
        },
        text_auto=".1f"
    )
    fig.update_yaxes(autorange="reversed")
    st.plotly_chart(fig, width='stretch')

    st.subheader("App Store category details")
    st.dataframe(category_view, width='stretch')

    st.subheader("Collected apps")
    app_columns = [
        column for column in [
            "snapshot_date", "category", "rank",
            "app_name", "developer", "app_url"
        ] if column in filtered_apps.columns
    ]
    st.dataframe(
        filtered_apps[app_columns].sort_values(
            ["category", "rank"]
        ),
        width='stretch',
        hide_index=True
    )

    st.download_button(
        "Download filtered App Store data",
        filtered_apps.to_csv(index=False),
        file_name="filtered_app_store_data.csv",
        mime="text/csv"
    )

st.divider()

# Section 3: Developer landscape
st.header("3. Developer landscape")

top_developers = developers.head(15).sort_values("unique_apps")

fig = px.bar(
    top_developers,
    x="unique_apps",
    y="developer",
    orientation="h",
    title="Developers with the most unique apps in the collected charts",
    labels={
        "unique_apps": "Unique apps",
        "developer": "Developer"
    }
)
st.plotly_chart(fig, width='stretch')

st.dataframe(developers.head(15), width='stretch')

st.divider()

# Section 4: Data limitations
st.header("4. Data coverage and limitations")

st.markdown("""
- Google Trends values are normalized relative-interest scores, not
  absolute search volumes.
- Search terms were collected separately, so their scores should not
  be interpreted as directly comparable market sizes.
- App Store chart rankings are ordinal positions, not downloads,
  revenue or active users.
- The App Store dataset contains two collection rounds approximately
  13 minutes apart. It does not provide enough historical variation
  to test festival-related ranking changes.
- The dashboard identifies patterns and potential planning signals;
  it does not establish that festivals caused changes in app rankings.
""")

st.subheader("Data coverage")

coverage = pd.DataFrame({
    "Dataset": ["Google Trends", "Apple App Store"],
    "Observations": [len(trends), len(apps)],
    "Unique items": [
        trends["keyword"].nunique(),
        apps["app_id"].nunique()
    ]
})

st.dataframe(coverage, width='stretch', hide_index=True)

st.caption(
    "Project: Festival & Cultural Seasonality Tracker | "
    "Data collected for India | Built with Python and Streamlit"
)
