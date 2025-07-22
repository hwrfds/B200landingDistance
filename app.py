import streamlit as st
import pandas as pd

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="B200 King Air Landing Distance Calculator",
    layout="centered"
)
st.title("B200 King Air Landing Distance Estimator")

# ─── Step 1: User inputs ─────────────────────────────────────────────────────
col1, col2 = st.columns(2)
with col1:
    press_alt = st.slider("Pressure Altitude (ft)", 0, 10000, 2000, 250)
    oat       = st.slider("OAT (°C)", -5, 45, 15, 1)
with col2:
    weight    = st.slider("Landing Weight (lb)", 9000, 12500, 11500, 100)
    wind      = st.slider(
        "Wind Speed (kt)", -20, 30, 0, 1,
        help="Negative = tailwind, Positive = headwind"
    )

# ─── Step 2: Table 1 – Pressure Height × OAT ─────────────────────────────────
raw1 = pd.read_csv("pressureheight_oat.csv", skiprows=[0])
raw1 = raw1.rename(
    columns={ raw1.columns[0]: "dummy", raw1.columns[1]: "PressAlt" }
)
tbl1 = (
    raw1
    .drop(columns=["dummy"])
    .set_index("PressAlt")
)
tbl1.columns = tbl1.columns.astype(int)

def lookup_tbl1(df, pa, t):
    # nearest‐below pressure altitude
    idx = max([i for i in df.index if i <= pa], default=df.index.min())
    # nearest‐below OAT
    hdr = max([h for h in df.columns if h <= t], default=df.columns.min())
    return df.loc[idx, hdr]

baseline = lookup_tbl1(tbl1, press_alt, oat)
st.markdown("### Step 1: Baseline")
st.write(f"- Pressure Altitude: **{press_alt} ft**")
st.write(f"- OAT: **{oat} °C**")
st.success(f"- Baseline distance: **{baseline:.0f} ft**")

# ─── Step 3: Table 2 – Weight Adjustment ─────────────────────────────────────
raw2 = pd.read_csv("weightadjustment.csv", skiprows=1, header=None)
wt_cols = raw2.iloc[0].astype(int).tolist()
df2 = raw2.iloc[1:].reset_index(drop=True).astype(float)
df2.columns = wt_cols

def lookup_tbl2(df, base, w):
    ref = df[12500]
    valid = ref[ref <= base]
    row = valid.index.max() if not valid.empty else 0
    return df.at[row, w]

weight_adj = lookup_tbl2(df2, baseline, weight)
st.markdown("### Step 2: Weight Adjustment")
st.write(f"- Baseline: **{baseline:.0f} ft**")
st.write(f"- Reference @ 12 500 lb: **{lookup_tbl2(df2, baseline, 12500):.0f} ft**")
st.write(f"- Landing Weight: **{weight} lb**")
st.success(f"- Weight‐adjusted: **{weight_adj:.0f} ft**")

# ─── Step 4: Table 3 – Wind Adjustment ───────────────────────────────────────
raw3 = pd.read_csv("wind adjustment.csv", header=None)
wind_cols = raw3.iloc[0].astype(int).tolist()
df3 = raw3.iloc[1:].reset_index(drop=True).astype(float)
df3.columns = wind_cols

def lookup_tbl3(df, refd, ws):
    ref0 = df[0]
    valid = ref0[ref0 <= refd]
    row = valid.index.max() if not valid.empty else 0
    return df.at[row, ws] - df.at[row, 0]

delta_wind = lookup_tbl3(df3, weight_adj, wind)
wind_adj   = weight_adj + delta_wind
st.markdown("### Step 3: Wind Adjustment")
st.write(f"- Before wind: **{weight_adj:.0f} ft**")
st.write(f"- Wind: **{wind:+.0f} kt** → Δ **{delta_wind:+.0f} ft**")
st.success(f"- After wind: **{wind_adj:.0f} ft**")

# ─── Step 5: Table 4 – 50 ft Obstacle Correction ─────────────────────────────
raw4 = pd.read_csv("50ft.csv", header=None)
cols4 = raw4.iloc[0].astype(int).tolist()   # [0, 50]
df4   = raw4.iloc[1:].reset_index(drop=True).astype(float)
df4.columns = cols4

def lookup_tbl4(df, rd):
    ref0 = df[0]
    valid = ref0[ref0 <= rd]
    row = valid.index.max() if not valid.empty else 0
    return df.at[row, 50]

obs50 = lookup_tbl4(df4, wind_adj)
st.markdown("### Step 4: 50 ft Obstacle")
st.write(f"- Before obstacle: **{wind_adj:.0f} ft**")
st.success(f"- Final over 50 ft obstacle: **{obs50:.0f} ft**")
