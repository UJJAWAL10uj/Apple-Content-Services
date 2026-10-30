import unittest
import pandas as pd
from tracker import normalize_trends_frame, event_window_metrics

class TrackerTests(unittest.TestCase):
    def test_normalize(self):
        df=pd.DataFrame({'date':['2026-10-01'],'keyword':['Diwali'],'geo':['IN'],'interest':[55]})
        out=normalize_trends_frame(df)
        self.assertEqual(int(out.iloc[0].interest),55)
        self.assertEqual(out.iloc[0].keyword,'Diwali')
    def test_event_metrics(self):
        dates=pd.date_range('2026-10-01',periods=45,freq='D')
        frame=pd.DataFrame({'date':dates,'interest':[20]*20+[60]*10+[25]*15})
        m=event_window_metrics(frame,'2026-10-31')
        self.assertIsNotNone(m['baseline_avg'])
        self.assertIsNotNone(m['event_avg'])
    def test_zero_baseline_pct_omitted(self):
        dates=pd.date_range('2026-10-01',periods=45,freq='D')
        frame=pd.DataFrame({'date':dates,'interest':[0]*45})
        m=event_window_metrics(frame,'2026-10-31')
        self.assertIsNone(m['lift_pct'])

if __name__=='__main__': unittest.main()
