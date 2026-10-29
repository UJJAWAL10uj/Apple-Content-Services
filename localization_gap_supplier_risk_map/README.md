# Localization Gap & Supplier Risk Map

A portfolio project that evaluates localization opportunities for an EV battery-module supply chain in India. It combines component-level import exposure, local supplier coverage, and supplier risk scoring into a small interactive dashboard.

> **Data status:** The included dataset is explicitly **illustrative / synthetic** so the project can be run before source verification. Do not describe the example values as real market research. The `source_register.csv` is a checklist for replacing each illustrative value with a traceable public source.

## Business questions
1. Which components appear most exposed to imports in the example scenario?
2. Where is Indian supplier coverage thin?
3. Which supplier risks should be addressed first?
4. What mitigations could reduce single-source, capacity, geopolitical, or quality-readiness exposure?

## Project contents
- `app.py` — Streamlit dashboard.
- `src/analyze.py` — risk scoring, component prioritization, and output exports.
- `data/component_localization.csv` — component-level scenario data.
- `data/suppliers.csv` — illustrative supplier records.
- `data/source_register.csv` — evidence tracker for public-source validation.
- `outputs/` — generated CSVs and chart images after running the analysis.
- `requirements.txt` — dependencies.

## Risk methodology
The dashboard uses a transparent weighted score from 0–100:
- Import exposure: 30%
- Single-source exposure: 25%
- Capacity risk: 20%
- Geopolitical / concentration risk: 15%
- Quality-readiness gap: 10%

Higher scores indicate greater risk / a stronger case for mitigation. Weights are **project assumptions**, not industry standards. Change them only with a clear rationale and document the change.

The example dataset's numeric values are synthetic and intended only to demonstrate the workflow. Replace them with researched values and cite the supporting source before using findings in a job application or interview.

## Run on Windows
Open PowerShell or Command Prompt in this project folder.

```bash
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
python -m src.analyze
streamlit run app.py
```

If PowerShell blocks activation, use Command Prompt, or run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.venv\Scripts\Activate.ps1
```

## Outputs
Running `python -m src.analyze` creates:
- `outputs/component_risk_scores.csv`
- `outputs/supplier_risk_scores.csv`
- `outputs/top_risks_and_mitigations.csv`
- `outputs/localization_gap_summary.md`

## How to replace synthetic data
1. Research component import reliance / local production using official government, customs, industry association, company annual report, or supplier product pages.
2. Add source URL, publication date, access date, metric definition, and confidence to `source_register.csv`.
3. Replace synthetic values only when the source actually supports the metric. If a source is qualitative, do not convert it into a precise percentage without explaining the method.
4. Add supplier names only when the supplier's product capability is supported by a public source. Record whether it is a manufacturer, distributor, or potential supplier.
5. Re-run the analysis and inspect the results before writing resume metrics.

## Important limitations
This is a screening tool, not a supplier audit or a verified import-substitution estimate. Public product pages do not prove available capacity, customer qualification, pricing, or quality performance. Treat these as validation tasks.
