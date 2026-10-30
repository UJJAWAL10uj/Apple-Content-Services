from __future__ import annotations
import argparse, json, re, time
from datetime import date, datetime, timezone
from pathlib import Path
import pandas as pd
import requests

ROOT=Path(__file__).resolve().parent
DATA=ROOT/"data"; REPORTS=ROOT/"reports"
CONFIG=json.loads((ROOT/"config.json").read_text(encoding="utf-8"))
CALENDAR=pd.read_csv(DATA/"festival_calendar.csv")

def normalize_trends_frame(frame: pd.DataFrame, fallback_keyword="Unspecified keyword"):
    f=frame.copy()
    f.columns=[str(c).strip().lower() for c in f.columns]
    date_col=next((c for c in f.columns if c in ("date","day","week","month","time")),None)
    value_col=next((c for c in f.columns if c in ("interest","value","search interest","diwali")),None)
    keyword_col=next((c for c in f.columns if c in ("keyword","query","search term","topic","term")),None)
    if not date_col or not value_col:
        # Google Trends export can have a title line before the real header; caller retries skiprows.
        raise ValueError("Could not identify date and interest/value columns.")
    if not keyword_col:
        f["keyword"]=fallback_keyword; keyword_col="keyword"
    out=pd.DataFrame({
      "date":pd.to_datetime(f[date_col],errors="coerce"),
      "keyword":f[keyword_col].astype(str),
      "geo":f["geo"].astype(str) if "geo" in f else "IN",
      "interest":pd.to_numeric(f[value_col].astype(str).str.replace("<1","0.5",regex=False),errors="coerce"),
      "source":f["source"].astype(str) if "source" in f else "Google Trends CSV export",
      "notes":f["notes"].astype(str) if "notes" in f else ""
    })
    return out.dropna(subset=["date","interest"]).sort_values(["keyword","date"])

def import_trends():
    folder=DATA/"google_trends"; folder.mkdir(exist_ok=True)
    frames=[]
    for path in folder.glob("*.csv"):
      try:
        raw=pd.read_csv(path)
        try: norm=normalize_trends_frame(raw,path.stem.replace("_"," "))
        except ValueError:
          raw=pd.read_csv(path,skiprows=1)
          norm=normalize_trends_frame(raw,path.stem.replace("_"," "))
        if norm["keyword"].eq("Unspecified keyword").all():
          norm["keyword"]=path.stem.replace("_"," ")
        frames.append(norm)
        print(f"Imported {len(norm)} rows: {path.name}")
      except Exception as e: print(f"Skipped {path.name}: {e}")
    template=DATA/"google_trends_template.csv"
    if template.exists() and template.stat().st_size>0:
      try:
        manual=normalize_trends_frame(pd.read_csv(template))
        frames.append(manual)
      except Exception: pass
    if not frames: raise SystemExit("No Trends data found. Add exports to data/google_trends/; see README.md.")
    out=pd.concat(frames,ignore_index=True).drop_duplicates(["date","keyword","geo"],keep="last")
    out.to_csv(DATA/"google_trends_normalized.csv",index=False)
    print(f"Saved {len(out)} normalized rows.")

def _apple_feed_entries(payload):
    """Accept Apple's RSS JSON whether feed/entry is a dict or a list."""
    feed = payload.get("feed", payload) if isinstance(payload, dict) else payload
    if isinstance(feed, list):
        # Some responses wrap the feed object in a one-element list.
        for item in feed:
            if isinstance(item, dict) and "entry" in item:
                entries = item.get("entry", [])
                return entries if isinstance(entries, list) else ([entries] if isinstance(entries, dict) else [])
        return [item for item in feed if isinstance(item, dict)]
    if isinstance(feed, dict):
        entries = feed.get("entry", [])
        return entries if isinstance(entries, list) else ([entries] if isinstance(entries, dict) else [])
    return []


def _apple_label(entry, key):
    """Safely read an Apple RSS label field."""
    value = entry.get(key, "") if isinstance(entry, dict) else ""
    if isinstance(value, list):
        value = value[0] if value else ""
    if isinstance(value, dict):
        return str(value.get("label", ""))
    return str(value) if value is not None else ""


def collect_apps():
    path=DATA/"app_chart_snapshots.csv"; rows=[]
    s=requests.Session(); s.headers.update({"User-Agent":"FestivalSeasonalityTracker/1.0 educational"})
    for i,cat in enumerate(CONFIG["categories"]):
      url=f"https://itunes.apple.com/{CONFIG['country']}/rss/{CONFIG['chart_type']}/limit={CONFIG['chart_limit']}/genre={cat['genre_id']}/json"
      try:
        r=s.get(url,timeout=CONFIG["timeout_seconds"]); r.raise_for_status()
        payload=r.json()
        entries=_apple_feed_entries(payload)
        for rank,e in enumerate(entries,1):
          if not isinstance(e,dict):
            continue
          link=_apple_label(e,"id")
          m=re.search(r"/id(\d+)",link)
          link_obj=e.get("link",{})
          if isinstance(link_obj,list): link_obj=link_obj[0] if link_obj else {}
          if not isinstance(link_obj,dict): link_obj={}
          attrs=link_obj.get("attributes",{})
          if not isinstance(attrs,dict): attrs={}
          app_url=attrs.get("href",link)
          rows.append({"snapshot_date":date.today().isoformat(),
           "collected_at_utc":datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "country":CONFIG["country"],"category":cat["name"],"genre_id":cat["genre_id"],
           "rank":rank,"app_id":m.group(1) if m else "","app_name":_apple_label(e,"im:name"),
           "developer":_apple_label(e,"im:artist"),"app_url":app_url})
        print(f"{cat['name']}: {len(entries)} entries ({sum(1 for x in rows if x['category']==cat['name'])} usable)")
      except Exception as e: print(f"ERROR {cat['name']}: {type(e).__name__}: {e}")
      if i<len(CONFIG["categories"])-1: time.sleep(.5)
    if not rows: raise SystemExit("No app chart data collected. Check internet, Apple's RSS response, and retry.")
    new=pd.DataFrame(rows)
    if path.exists(): new=pd.concat([pd.read_csv(path),new],ignore_index=True)
    new=new.drop_duplicates(["snapshot_date","category","rank","app_id"],keep="last")
    new.to_csv(path,index=False)
    print(f"App chart history saved: {len(new)} rows across {new.snapshot_date.nunique()} dates.")

def event_window_metrics(frame,event_date):
    f=frame.copy(); f["date"]=pd.to_datetime(f["date"])
    d=pd.Timestamp(event_date)
    baseline=f[(f.date>=d-pd.Timedelta(days=30))&(f.date<=d-pd.Timedelta(days=15))]
    event=f[(f.date>=d-pd.Timedelta(days=7))&(f.date<=d+pd.Timedelta(days=3))]
    b=baseline.interest.mean() if len(baseline) else None
    e=event.interest.mean() if len(event) else None
    lift=e-b if b is not None and e is not None else None
    pct=(lift/b*100) if lift is not None and b>0 else None
    return {"baseline_avg":b,"event_avg":e,"lift_points":lift,"lift_pct":pct,
            "baseline_observations":len(baseline),"event_observations":len(event)}

def analyze():
    trends_file=DATA/"google_trends_normalized.csv"
    if not trends_file.exists(): raise SystemExit("Run import-trends first; see README.md.")
    trends=pd.read_csv(trends_file,parse_dates=["date"])
    if trends.empty: raise SystemExit("Trends dataset is empty.")
    rows=[]
    for _,ev in CALENDAR.iterrows():
      for term in str(ev.search_terms).split(";"):
        # allow exact keyword match only to avoid silently attributing a different phrase
        subset=trends[trends.keyword.str.casefold()==term.strip().casefold()]
        if subset.empty: continue
        metrics=event_window_metrics(subset,ev.event_date)
        rows.append({"event_id":ev.event_id,"event":ev.event_name,"event_date":ev.event_date,
          "region":ev.region,"keyword":term.strip(),**metrics})
    event_df=pd.DataFrame(rows)
    if event_df.empty:
      raise SystemExit("No imported keyword exactly matches festival_calendar.csv search_terms. Align exported keyword names or edit the calendar.")
    REPORTS.mkdir(exist_ok=True)
    event_df.to_csv(REPORTS/"event_search_summary.csv",index=False)
    app_file=DATA/"app_chart_snapshots.csv"
    if app_file.exists():
      apps=pd.read_csv(app_file,parse_dates=["snapshot_date"])
      app_summary=apps.groupby(["category","snapshot_date"]).agg(
        app_count=("app_id","nunique"),mean_rank=("rank","mean"),median_rank=("rank","median")).reset_index()
      # Latest vs prior observed snapshot per category.
      app_summary=app_summary.sort_values(["category","snapshot_date"])
      app_summary["previous_mean_rank"]=app_summary.groupby("category").mean_rank.shift(1)
      app_summary["mean_rank_change"]=app_summary.previous_mean_rank-app_summary.mean_rank
    else: app_summary=pd.DataFrame()
    event_dates=CALENDAR[["event_id","event_name","event_type","event_date","region","date_status"]].copy()
    with pd.ExcelWriter(REPORTS/"festival_seasonality.xlsx",engine="openpyxl") as writer:
      event_dates.to_excel(writer,sheet_name="Event Calendar",index=False)
      trends.to_excel(writer,sheet_name="Google Trends",index=False)
      event_df.to_excel(writer,sheet_name="Event Search Analysis",index=False)
      if not app_summary.empty: app_summary.to_excel(writer,sheet_name="App Category Trends",index=False)
      for ws in writer.book.worksheets:
        ws.freeze_panes="A2"; ws.auto_filter.ref=ws.dimensions
        for col in ws.columns:
          width=min(max(max(len(str(c.value or "")) for c in col[:300])+2,10),42)
          ws.column_dimensions[col[0].column_letter].width=width
    earliest=trends.date.min().date(); latest=trends.date.max().date()
    top=event_df.dropna(subset=["lift_points"]).sort_values("lift_points",ascending=False).head(10)
    lines=["# Festival & Cultural Seasonality — Intelligence Brief","",
      f"- **Data range:** {earliest} to {latest}",
      f"- **Keywords:** {trends.keyword.nunique()}",
      f"- **Search observations:** {len(trends)}",
      f"- **Events with matched keyword data:** {event_df.event.nunique()}","",
      "## Largest event-window search lifts",""]
    if top.empty: lines.append("Not enough baseline/event-window data to calculate lifts.")
    for _,r in top.iterrows():
      pct=f" ({r.lift_pct:.1f}% vs baseline)" if pd.notna(r.lift_pct) else ""
      lines.append(f"- **{r.event} / {r.keyword}:** {r.lift_points:.1f} Trends index points{pct}.")
    lines += ["","## Interpretation limits",
      "- Trends is a normalized relative-interest index, not absolute search volume.",
      "- Independently scaled exports should not be compared directly across keywords.",
      "- Event-window lift is association, not causation.",
      "- Validate local festival dates and observances before publishing.",
      "- App Store chart rank is a visibility proxy, not downloads, revenue, or user behaviour."]
    (REPORTS/"weekly_intelligence_brief.md").write_text("\\n".join(lines)+"\\n",encoding="utf-8")
    print("Created reports/festival_seasonality.xlsx and weekly_intelligence_brief.md")

def main():
  p=argparse.ArgumentParser(description="India Festival & Cultural Seasonality Tracker")
  p.add_argument("command",choices=["collect-apps","import-trends","analyze"])
  c=p.parse_args().command
  {"collect-apps":collect_apps,"import-trends":import_trends,"analyze":analyze}[c]()

if __name__=="__main__": main()
