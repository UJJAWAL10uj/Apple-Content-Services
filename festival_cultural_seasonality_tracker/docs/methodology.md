# Methodology

## Design
Observational time-series study using public search-interest indices and public app chart snapshots.

## Event windows
- Baseline: event date -30 through -15 days.
- Event period: event date -7 through +3 days.
- Lift points: event-period mean minus baseline mean.
- Relative lift: lift / baseline mean, only if baseline mean > 0.

## App rankings
Rank 1 is highest. Daily snapshots are appended. Compare only observed dates; missing days remain missing. A current feed does not provide historical chart history.

## Quality checks
- Keep original exports unchanged.
- Record geography, search type, query, and extraction date.
- Verify festival date and regional observance.
- Inspect data coverage and missing dates.
- Never treat Trends index as absolute volume.
- Do not infer causation from temporal coincidence.
