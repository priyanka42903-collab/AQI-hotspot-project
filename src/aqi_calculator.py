import numpy as np
import pandas as pd

CPCB_BREAKPOINTS = {
    'PM2.5': [(0,30,0,50),(31,60,51,100),(61,90,101,200),(91,120,201,300),(121,250,301,400),(251,380,401,500)],
    'PM10':  [(0,50,0,50),(51,100,51,100),(101,250,101,200),(251,350,201,300),(351,430,301,400),(431,600,401,500)],
    'NO2':   [(0,40,0,50),(41,80,51,100),(81,180,101,200),(181,280,201,300),(281,400,301,400),(401,500,401,500)],
    'SO2':   [(0,40,0,50),(41,80,51,100),(81,380,101,200),(381,800,201,300),(801,1600,301,400),(1601,2000,401,500)],
    'CO':    [(0,1.0,0,50),(1.1,2.0,51,100),(2.1,10,101,200),(10.1,17,201,300),(17.1,34,301,400),(34.1,50,401,500)],
    'O3':    [(0,50,0,50),(51,100,51,100),(101,168,101,200),(169,208,201,300),(209,748,301,400),(749,1000,401,500)],
}
POLLUTANTS = list(CPCB_BREAKPOINTS)


def sub_index(pollutant, conc):
    """CPCB sub-index. Uses the first band whose upper limit is >= conc,
    so values falling in the small gaps between bands are still scored."""
    if pd.isna(conc) or conc < 0:
        return np.nan
    bands = CPCB_BREAKPOINTS[pollutant]
    for c_lo, c_hi, i_lo, i_hi in bands:
        if conc <= c_hi:
            c = max(conc, c_lo)
            return (i_hi - i_lo) / (c_hi - c_lo) * (c - c_lo) + i_lo
    return 500.0


def sub_index_frame(df):
    return pd.DataFrame(
        {p: df[p].map(lambda c, p=p: sub_index(p, c)) for p in POLLUTANTS if p in df.columns},
        index=df.index)


def aqi_and_dominant(df, min_pollutants=3, require_pm=True):
    sub = sub_index_frame(df)
    ok = sub.notna().sum(axis=1) >= min_pollutants
    if require_pm:
        ok = ok & sub[['PM2.5', 'PM10']].notna().any(axis=1)
    aqi = sub.max(axis=1).where(ok)
    dominant = sub.fillna(-1).idxmax(axis=1).where(ok)
    return aqi, dominant