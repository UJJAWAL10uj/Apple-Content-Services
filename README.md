
# Apple-Focused Product, Market & Operations Intelligence Portfolio

A collection of four data-driven projects exploring India's digital ecosystem, supply-chain localization, consumer experience, and cultural seasonality. These projects combine Python, Excel, interactive dashboards, and structured research to turn data into actionable business insights.

## Portfolio Overview

| # | Project | Core Focus | Key Tools |
|---|---|---|---|
| 1 | India App Category & Mobile Gaming Intelligence Tracker | App-market intelligence and category analysis | Python, Pandas, CSV |
| 2 | Localization Gap & Supplier Risk Map | Supply-chain localization and supplier risk | Python, Pandas, Excel, Streamlit |
| 3 | Platform Benchmark & User-Flow Teardown | Competitor benchmarking and UX analysis | Excel, Python, Streamlit |
| 4 | Festival & Cultural Seasonality Tracker | Search-interest trends and seasonal planning | Python, Pandas, Excel, Google Trends, Streamlit |

---

## 1. India App Category & Mobile Gaming Intelligence Tracker

**Objective:** Build a structured view of India's app ecosystem to explore category-level competition, app metadata, and mobile gaming opportunities.

### Project Highlights
- Organizes app-ranking observations across eight categories: Games, Social Networking, Entertainment, Photo & Video, Education, Health & Fitness, Finance, and Lifestyle.
- Structures app metadata for category-level comparisons.
- Supports investigation of app-market positioning and category patterns.
- Provides a foundation for identifying potential opportunities in India's mobile gaming and digital app ecosystem.

**Tools:** Python, Pandas, CSV, Data Analysis

**Business Applications**
- App-category and competitor intelligence.
- Early-stage market opportunity assessment.
- Digital product research and category prioritization.

**Data Note:** A single collected snapshot provides a point-in-time view. Longitudinal trends should only be claimed when data has been collected across multiple dates.

---

## 2. Localization Gap & Supplier Risk Map

**Objective:** Develop a structured screening framework to identify component localization gaps and assess potential supplier risks.

### Project Highlights
- Organizes component-level localization and supplier information.
- Evaluates potential supplier risk using a weighted screening framework.
- Compares import exposure, single-source dependency, capacity risk, geopolitical exposure, and quality gaps.
- Generates processed datasets and an interactive Streamlit dashboard.

### Risk Assessment Framework

| Risk Factor | Weight |
|---|---:|
| Import exposure | 30% |
| Single-source dependency | 25% |
| Capacity risk | 20% |
| Geopolitical exposure | 15% |
| Quality gap | 10% |

**Tools:** Python, Pandas, Excel, Streamlit, Data Visualization

**Business Applications**
- Supplier-risk screening.
- Localization opportunity assessment.
- Supply-chain resilience and sourcing discussions.
- Prioritization of components for further investigation.

**Data Note:** The initial supplier records and numerical inputs are synthetic and illustrative. The risk score is a screening model based on stated assumptions, not an official industry benchmark or a verified assessment of Apple's actual suppliers.

---

## 3. Platform Benchmark & User-Flow Teardown

**Objective:** Build a repeatable competitor-benchmarking framework to examine food-ordering journeys, identify potential user friction, and structure UX improvement opportunities.

### Competitors
- Zomato
- Swiggy
- Domino's India
- EatSure

### Project Highlights
- Structures public app-store and official website research into a competitor audit.
- Maps the expected journey from location selection and discovery to menu selection, cart, checkout, order tracking, and support.
- Maintains a friction log with hypotheses and validation protocols.
- Provides a UX scorecard framework for evaluating usability criteria.
- Organizes evidence links and research limitations.

**Tools:** Excel, Python, Pandas, Streamlit, Public-Source Research

**Business Applications**
- Competitor feature benchmarking.
- User-journey analysis.
- Checkout and conversion-funnel investigation.
- Prioritization of UX research and product improvements.

**Methodology Note:** Publicly supported findings are separated from hypotheses. Live UX scores, checkout fees, timings, and screen-level observations should only be reported after direct testing and evidence capture.

---

## 4. Festival & Cultural Seasonality Tracker

**Objective:** Analyze how search interest around Indian festivals and cultural events changes over time to support seasonal marketing and category-planning decisions.

### Events and Themes
- Diwali
- Holi
- Pongal
- Navratri
- Onam
- Eid
- Christmas
- IPL

### Project Highlights
- Organizes festival keywords and event dates into structured datasets.
- Uses Google Trends exports to analyze relative search interest over time.
- Compares pre-event, event-week, and post-event periods.
- Calculates baseline interest, relative uplift, and peak-interest periods when sufficient data is available.
- Supports analysis through Python, Excel templates, and an interactive dashboard.

**Tools:** Python, Pandas, Excel, Google Trends, Streamlit, Data Visualization

**Business Applications**
- Seasonal campaign planning.
- Content and keyword planning.
- Event-driven demand research.
- Identification of potential seasonal opportunities.

**Data Note:** Google Trends reports normalized relative search interest, not absolute search volume or sales. Demonstration data must be labelled synthetic; conclusions should be based on actual exports and documented event dates.

---

## Technology Stack

| Category | Technologies |
|---|---|
| Programming | Python |
| Data manipulation | Pandas |
| Data storage and exchange | CSV, Excel |
| Interactive dashboards | Streamlit |
| Research and data inputs | Public app-store listings, official websites, Google Trends exports |
| Analysis methods | Descriptive analytics, weighted risk screening, competitor benchmarking, time-window comparison |

## Repository Structure

```text
apple-focused-analytics-portfolio/
│
├── README.md
│
├── india_app_category_gaming_tracker/
│   ├── data/
│   ├── src/
│   ├── outputs/
│   └── README.md
│
├── localization_gap_supplier_risk_map/
│   ├── data/
│   ├── src/
│   ├── outputs/
│   ├── app.py
│   └── README.md
│
├── platform_benchmark_user_flow_teardown/
│   ├── data/
│   ├── app.py
│   ├── outputs/
│   ├── Platform_Benchmark_User_Flow_Teardown.xlsx
│   └── README.md
│
└── festival_cultural_seasonality_tracker/
    ├── data/
    ├── templates/
    ├── src/
    ├── outputs/
    ├── app.py
    └── README.md
```

## Key Takeaways

Together, these projects demonstrate a practical approach to:

- **Market intelligence:** Structuring app-category and competitor data.
- **Operations analytics:** Building a transparent supplier-risk screening framework.
- **Product analytics:** Mapping user journeys and organizing UX benchmarking.
- **Growth analytics:** Investigating cultural seasonality and search-interest patterns.
- **Decision support:** Converting research and datasets into structured workbooks, repeatable analysis, and interactive dashboards.

The emphasis throughout is on transparent methodology, reproducible analysis, evidence-backed conclusions, and a clear distinction between observed facts, assumptions, and hypotheses.

---

## Disclaimer

These are independent portfolio projects for analytical and educational purposes. They do not represent official Apple research, proprietary Apple data, or an endorsement by Apple Inc. Synthetic data is used for demonstration only and should not be interpreted as actual company or industry performance.
