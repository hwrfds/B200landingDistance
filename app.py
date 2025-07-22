import streamlit as st
import pandas as pd

# ─── Page Setup ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="B200 Landing Distance Calculator", layout="centered")
st.title("B200 King Air Landing Distance Estimator")

# ─── Step 1: User Inputs ────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    press_alt = st.slider("Pressure Altitude (ft)", 0, 10000, 2000, 250)
    oat       = st.slider("Outside Air Temperature (°C)", -5, 45, 15, 1)
with col2:
    weight    = st.slider("Landing Weight (lb)", 9000, 12500, 11500, 100)
    wind      = st.slider("Wind Speed (kt)", -20, 30, 0, 1,
                          help="Negative = tailwind, Positive = headwind")

# ─── Step 2: Table 1 – Pressure-Height × OAT ────────────────────────────────
raw1 = pd.read_csv("pressureheight_oat.csv", skiprows=[0])
raw1 = raw1.rename(columns={ raw1.columns[0]: "dummy", raw1.columns[1]: "PressAlt" })
tbl1 = raw1.drop(columns=["dummy"]).set_index("PressAlt")
tbl1.columns = tbl1.columns.astype(int)

def lookup_tbl1(df, pa, t):
    idx = max([i for i in df.index if i <= pa], default=df.index.min())
    hdr = max([h for h in df.columns if h <= t], default=df.columns.min())
    return df.loc[idx, hdr]

baseline = lookup_tbl1(tbl1, press_alt, oat)
st.markdown("### Step 1: Baseline Distance")
st.write(f"Pressure Altitude: **{press_alt} ft**  \nOAT: **{oat} °C**")
st.success(f"Baseline landing distance: **{baseline:.0f} ft**")

# ─── Step 3: Table 2 – Weight Adjustment ────────────────────────────────────
raw2 = pd.read_csv("weightadjustment.csv", header=0)
wt_cols = [int(str(w).strip()) for w in raw2.columns]
df2 = raw2.astype(float)
df2.columns = wt_cols

def lookup_tbl2(df, base, w):
    if 12500 not in df.columns:
