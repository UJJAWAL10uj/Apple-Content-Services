
import pandas as pd

df = pd.read_csv("data/festival_calendar.csv")

print("\n========== FESTIVAL CALENDAR ==========")
print("Rows:", len(df))
print("Columns:", df.columns.tolist())
print("\nFestival records:")
print(df.to_string(index=False))
print("\n========== COMPLETE ==========")
