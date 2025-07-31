import streamlit as st
import pandas as pd

# ─── Page Setup ─────────────────────────────────────────────────────────────
st.set_page_config(page_title="B200 Landing Distance Calculator", layout="centered")
st.title("B200 King Air Landing Distance Estimator")
st.sidebar.title("Landing Performance Inputs")  # Larger, bold title

# ─── Step 1: User Inputs ────────────────────────────────────────────────────
press_alt = st.sidebar.slider("Pressure Altitude (ft)", 0, 10000, 2000, 250)
oat       = st.sidebar.slider("Outside Air Temperature (°C)", -5, 45, 15, 1)
weight    = st.sidebar.slider("Landing Weight (lb)", 9000, 12500, 11500, 100)
wind      = st.sidebar.slider("Wind Speed (kt)", -20, 30, 0, 1,
                              help="Negative = tailwind, Positive = headwind")



st.sidebar.info("**Associated Conditions**  \n"
                "**POWER** – Retard to Maintain 1000ft/m on final app  \n"
                "**FLAPS** – 100%  \n"
                "**RUNWAY** – Paved, Level, Dry Surface  \n"
                "**Approach Speed** – As tabulated  \n"
                "**Braking** – Maximum  \n"
                "**Condition Levers** – High Idle  \n"
                "**Propellor Controls** – Full Forward  \n"
                "**Power Levers** – Max Reverse After Touchdown Until Fully Stopped")

st.sidebar.markdown(f"""
**App IAS**

| Weight lbs       | App Speed KTS|
|------------------|--------------|
| 12,500           | 103          |
| 12,000           | 102          |
| 11,000           | 99           |
| 10,000           | 96           |
| 9,000            | 93           |
""")


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
        st.error("Column 12500 lb not found in Table 2 headers.")
        st.stop()
    ref = df[12500]
    valid = ref[ref <= base]
    row = valid.index.max() if not valid.empty else 0
    if w not in df.columns:
        st.error(f"Selected weight {w} lb not found in table.")
        st.stop()
    return df.at[row, w]

weight_adj = lookup_tbl2(df2, baseline, weight)
st.markdown("### Step 2: Weight Adjustment")
st.write(f"Selected Weight: **{weight} lb**")
st.success(f"Weight-adjusted distance: **{weight_adj:.0f} ft**")

# ─── Step 4: Table 3 – Wind Adjustment ──────────────────────────────────────
raw3 = pd.read_csv("wind adjustment.csv", header=None)
wind_cols = [int(str(w).strip()) for w in raw3.iloc[0]]
df3 = raw3.iloc[1:].reset_index(drop=True).astype(float)
df3.columns = wind_cols

def lookup_tbl3(df, refd, ws):
    ref0 = df[0]
    valid = ref0[ref0 <= refd]
    row = valid.index.max() if not valid.empty else 0
    if ws not in df.columns:
        st.error(f"Wind speed {ws} kt not found in table.")
        st.stop()
    return df.at[row, ws] - df.at[row, 0]

delta_wind = lookup_tbl3(df3, weight_adj, wind)
wind_adj   = weight_adj + delta_wind
st.markdown("### Step 3: Wind Adjustment")
st.write(f"Wind: **{wind:+.0f} kt** → Δ: **{delta_wind:+.0f} ft**")
st.success(f"After wind adjustment: **{wind_adj:.0f} ft**")

# ─── Step 5: Table 4 – 50 ft Obstacle Correction ────────────────────────────
raw4 = pd.read_csv("50ft.csv", header=None)
obs_cols = [int(str(c).strip()) for c in raw4.iloc[0]]
df4 = raw4.iloc[1:].reset_index(drop=True).astype(float)
df4.columns = obs_cols

def lookup_tbl4(df, refd):
    ref0 = df[0]
    valid = ref0[ref0 <= refd]
    row = valid.index.max() if not valid.empty else 0
    return df.at[row, 50]

obs50 = lookup_tbl4(df4, wind_adj)
st.markdown("### Step 4: 50 ft Obstacle Correction")
st.success(f"Final landing distance over 50 ft obstacle: **{obs50:.0f} ft**")
