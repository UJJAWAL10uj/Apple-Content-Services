from pathlib import Path
import pandas as pd
import plotly.express as px
import streamlit as st
from src.analyze import score_components, mitigation_for

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

st.set_page_config(page_title="Localization Gap & Supplier Risk Map", layout="wide")
st.title("Localization Gap & Supplier Risk Map")
st.caption("EV battery-module supply chain | India | Portfolio prototype")

st.warning(
    "Starter data is illustrative / synthetic, not verified market research. "
    "Use this dashboard to test the workflow; replace the inputs with sourced evidence before citing findings."
)

components = pd.read_csv(DATA / "component_localization.csv")
suppliers = pd.read_csv(DATA / "suppliers.csv")
scored = score_components(components)
scored["recommended_mitigation"] = scored.apply(mitigation_for, axis=1)

c1, c2, c3 = st.columns(3)
c1.metric("Components mapped", f"{len(scored)}")
c2.metric("Higher-risk components", int((scored["risk_band"] == "Higher").sum()))
c3.metric("Supplier records", f"{len(suppliers)}")

st.subheader("Component risk ranking")
fig = px.bar(
    scored.sort_values("risk_score_0_100"),
    x="risk_score_0_100", y="component", color="risk_band", orientation="h",
    labels={"risk_score_0_100": "Screening risk score (0–100)", "component": ""},
    hover_data=["illustrative_import_share_pct", "illustrative_single_source_exposure_pct", "confidence"],
)
st.plotly_chart(fig, use_container_width=True)

left, right = st.columns(2)
with left:
    st.subheader("Import exposure vs single-source exposure")
    scatter = px.scatter(
        scored, x="illustrative_import_share_pct", y="illustrative_single_source_exposure_pct",
        size="annual_demand_units", color="risk_band", hover_name="component",
        labels={
            "illustrative_import_share_pct": "Illustrative import share (%)",
            "illustrative_single_source_exposure_pct": "Illustrative single-source exposure (%)",
        },
    )
    st.plotly_chart(scatter, use_container_width=True)
with right:
    st.subheader("Top risk mitigations")
    st.dataframe(
        scored[["component", "risk_score_0_100", "risk_band", "recommended_mitigation"]].head(5),
        use_container_width=True, hide_index=True
    )

st.subheader("Component-level data")
st.dataframe(scored, use_container_width=True, hide_index=True)

st.subheader("Supplier risk register")
st.caption("Supplier names in the starter data are placeholders, not real supplier recommendations.")
supplier_view = suppliers.copy()
supplier_view["evidence_status"] = supplier_view["public_capability_evidence"].apply(
    lambda x: "Needs verification" if str(x).strip().lower() in {"not yet verified", "", "nan"} else "Evidence recorded"
)
st.dataframe(supplier_view, use_container_width=True, hide_index=True)

st.subheader("Download current outputs")
st.download_button(
    "Download component risk scores (CSV)",
    scored.to_csv(index=False).encode("utf-8"),
    file_name="component_risk_scores.csv",
    mime="text/csv",
)
st.download_button(
    "Download supplier register (CSV)",
    suppliers.to_csv(index=False).encode("utf-8"),
    file_name="supplier_register.csv",
    mime="text/csv",
)
