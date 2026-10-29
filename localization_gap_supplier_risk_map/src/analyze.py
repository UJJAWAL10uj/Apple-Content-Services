from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"

WEIGHTS = {
    "import_exposure": 0.30,
    "single_source": 0.25,
    "capacity": 0.20,
    "geopolitical": 0.15,
    "quality_gap": 0.10,
}

def score_components(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate an interpretable 0-100 screening score. Inputs are illustrative until sourced."""
    out = df.copy()
    out["import_exposure_score"] = out["illustrative_import_share_pct"].clip(0, 100)
    out["single_source_score"] = out["illustrative_single_source_exposure_pct"].clip(0, 100)
    out["capacity_score"] = (out["capacity_risk_1_5"].clip(1, 5) - 1) / 4 * 100
    out["geopolitical_score"] = (out["geopolitical_concentration_risk_1_5"].clip(1, 5) - 1) / 4 * 100
    out["quality_gap_score"] = (out["quality_readiness_gap_1_5"].clip(1, 5) - 1) / 4 * 100
    out["risk_score_0_100"] = (
        out["import_exposure_score"] * WEIGHTS["import_exposure"]
        + out["single_source_score"] * WEIGHTS["single_source"]
        + out["capacity_score"] * WEIGHTS["capacity"]
        + out["geopolitical_score"] * WEIGHTS["geopolitical"]
        + out["quality_gap_score"] * WEIGHTS["quality_gap"]
    ).round(1)
    out["risk_band"] = pd.cut(
        out["risk_score_0_100"],
        bins=[-0.1, 33.3, 66.6, 100],
        labels=["Lower", "Medium", "Higher"],
        include_lowest=True,
    ).astype(str)
    return out.sort_values("risk_score_0_100", ascending=False)

def mitigation_for(row: pd.Series) -> str:
    actions = []
    if row["illustrative_single_source_exposure_pct"] >= 50:
        actions.append("Qualify a second source; document switching lead time")
    if row["capacity_risk_1_5"] >= 4:
        actions.append("Run capacity audit and request a ramp-up plan")
    if row["geopolitical_concentration_risk_1_5"] >= 4:
        actions.append("Diversify country-of-origin exposure and map sub-tier inputs")
    if row["quality_readiness_gap_1_5"] >= 4:
        actions.append("Complete APQP/PPAP-style validation and process capability review")
    if row["illustrative_import_share_pct"] >= 60:
        actions.append("Evaluate localization economics and tooling / qualification costs")
    if not actions:
        actions.append("Monitor quarterly; validate cost, capacity, and quality evidence")
    return "; ".join(dict.fromkeys(actions))

def main():
    OUT.mkdir(exist_ok=True)
    components = pd.read_csv(DATA / "component_localization.csv")
    suppliers = pd.read_csv(DATA / "suppliers.csv")

    scored = score_components(components)
    scored["recommended_mitigation"] = scored.apply(mitigation_for, axis=1)
    scored.to_csv(OUT / "component_risk_scores.csv", index=False)

    supplier_scored = suppliers.copy()
    supplier_scored["supplier_risk_score_0_100"] = (
        (6 - supplier_scored["capacity_confidence_1_5"].clip(1, 5)) / 4 * 35
        + (6 - supplier_scored["quality_readiness_1_5"].clip(1, 5)) / 4 * 30
        + (supplier_scored["geopolitical_risk_1_5"].clip(1, 5) - 1) / 4 * 20
        + supplier_scored["single_source_flag"].map({"Yes": 100, "No": 0}).fillna(50) * 0.15
    ).round(1)
    supplier_scored["evidence_status"] = supplier_scored["public_capability_evidence"].apply(
        lambda x: "Needs verification" if str(x).strip().lower() in {"not yet verified", "", "nan"} else "Evidence recorded"
    )
    supplier_scored.to_csv(OUT / "supplier_risk_scores.csv", index=False)

    top = scored[[
        "component_id", "component", "risk_score_0_100", "risk_band",
        "illustrative_import_share_pct", "illustrative_single_source_exposure_pct",
        "recommended_mitigation", "confidence"
    ]].head(3)
    top.to_csv(OUT / "top_risks_and_mitigations.csv", index=False)

    lines = [
        "# Localization Gap & Supplier Risk Map — Latest Run",
        "",
        "> **Important:** All numerical input data in this starter version is illustrative / synthetic. These results are not verified market findings.",
        "",
        f"Components assessed: **{len(scored)}**",
        f"Supplier records assessed: **{len(supplier_scored)}**",
        "",
        "## Highest-priority illustrative components",
        "",
        top.to_markdown(index=False),
        "",
        "## Scoring",
        "Risk score is a weighted screening score from 0–100. Weights: import exposure 30%, single-source exposure 25%, capacity risk 20%, geopolitical concentration risk 15%, quality-readiness gap 10%. These are project assumptions.",
        "",
        "## Data quality checklist",
        "- Replace illustrative component data with sourced evidence.",
        "- Verify supplier capability through public product pages, annual reports, or certifications.",
        "- Keep source URL, publication date, access date, units, and caveats in `data/source_register.csv`.",
        "- Do not describe the synthetic values as observed industry statistics.",
        "",
    ]
    (OUT / "localization_gap_summary.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"Analysis complete. Components: {len(scored)}; supplier records: {len(supplier_scored)}")
    print(f"Outputs written to: {OUT}")
    print("Reminder: starter data is illustrative and must be verified before making factual claims.")

if __name__ == "__main__":
    main()
