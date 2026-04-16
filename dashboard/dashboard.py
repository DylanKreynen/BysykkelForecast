"""
Oslo Bysykkel – 9-Day Forecast Dashboard
Run with:  streamlit run dashboard.py
"""

import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import base64

# ── Brand tokens ───────────────────────────────────────────────────────────────
BLUE        = "#005FC9"   # primary brand blue
BLUE_HOVER  = "#004796"
BLUE_LIGHT  = "#E8F0FB"   # tint for fills
NAVY        = "#0B163F"   # body / headings
GRAY_BG     = "#F5F8F9"   # page background
GRAY_MID    = "#E3E6EB"   # card borders
GRAY_DIM    = "#72718E"   # secondary text
WHITE       = "#FFFFFF"
ORANGE      = "#E8622A"   # temperature accent
PRECIP_BLUE = "#7BB3E8"   # precipitation bars
GREEN       = "#2DA35E"   # wind
FONT_STACK  = '"Urban Grotesk", "Helvetica Neue", Arial, sans-serif'

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bysykkel Forecast",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(f"""
<style>
  /* ---- Font ---- */
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

  html, body, [class*="css"], .stMarkdown, .stMetric,
  .stDataFrame, .stExpander, button, input, select {{
    font-family: {FONT_STACK};
    color: {NAVY};
  }}

  /* ---- Page background ---- */
  .stApp {{ background-color: {GRAY_BG}; }}
  .block-container {{
    padding-top: 0 !important;
    padding-bottom: 3rem;
    max-width: 1300px;
  }}

  /* ---- Hero header ---- */
  .hero {{
    background-color: {NAVY};
    padding: 36px 48px 32px 48px;
    margin: -1px -1px 0 -1px;           /* bleed to edges */
    border-radius: 0;
  }}
  .hero-wordmark {{
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 6px;
  }}
  .hero-logo-ring {{
    width: 44px; height: 44px;
    border-radius: 8px;
    background: {WHITE};
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    overflow: hidden;
    padding: 0;
    box-sizing: border-box;
  }}
  .hero-brand {{
    font-size: 26px;
    font-weight: 400;
    color: {WHITE} !important;
    letter-spacing: -0.3px;
  }}
  .hero-title {{
    font-size: 40px !important;
    font-weight: 700 !important;
    color: {WHITE} !important;
    line-height: 1.15 !important;
    margin: 0 0 8px 0 !important;
    letter-spacing: -0.5px !important;
    font-family: {FONT_STACK} !important;
  }}
  .hero-sub {{
    font-size: 16px;
    color: rgba(255,255,255,0.65) !important;
    margin: 0;
    font-weight: 400;
  }}
  .hero-pill {{
    display: inline-block;
    margin-top: 18px;
    background: {BLUE};
    color: {WHITE};
    font-size: 13px;
    font-weight: 600;
    padding: 5px 16px;
    border-radius: 9999px;
    letter-spacing: 0.2px;
  }}

  /* ---- Section heading ---- */
  .section-heading {{
    font-size: 22px;
    font-weight: 700;
    color: {NAVY};
    margin: 36px 0 4px 0;
    letter-spacing: -0.2px;
  }}
  .section-sub {{
    font-size: 14px;
    color: {GRAY_DIM};
    margin: 0 0 16px 0;
  }}

  /* ---- KPI cards ---- */
  .kpi-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 12px;
    margin: 24px 0 0 0;
    width: 100%;
  }}
  .kpi-card {{
    background: {WHITE};
    border: 1px solid {GRAY_MID};
    border-radius: 10px;
    padding: 20px 20px 18px 20px;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }}
  .kpi-label {{
    font-size: 12px;
    font-weight: 600;
    color: {GRAY_DIM};
    text-transform: uppercase;
    letter-spacing: 0.6px;
  }}
  .kpi-value {{
    font-size: 28px;
    font-weight: 700;
    color: {NAVY};
    line-height: 1.1;
    letter-spacing: -0.5px;
  }}
  .kpi-value span {{
    font-size: 14px;
    font-weight: 500;
    color: {GRAY_DIM};
    margin-left: 2px;
  }}
  .kpi-accent {{ color: {BLUE}; }}

  /* ---- Divider ---- */
  .bysykkel-divider {{
    border: none;
    border-top: 1px solid {GRAY_MID};
    margin: 32px 0;
  }}

  /* ---- Chart cards ---- */
  .chart-card {{
    background: {WHITE};
    border: 1px solid {GRAY_MID};
    border-radius: 10px;
    padding: 24px 20px 16px 20px;
    margin-bottom: 16px;
  }}

  /* ---- Table ---- */
  .stDataFrame thead tr th {{
    background-color: {NAVY} !important;
    color: {WHITE} !important;
    font-weight: 600;
    font-size: 13px;
  }}
  .stDataFrame tbody tr:nth-child(even) {{ background: {GRAY_BG}; }}

  /* ---- Expander ---- */
  .streamlit-expanderHeader {{
    font-weight: 600;
    font-size: 15px;
    color: {NAVY};
    background: {WHITE};
    border: 1px solid {GRAY_MID};
    border-radius: 10px;
  }}
  .streamlit-expanderContent {{
    background: {WHITE};
    border: 1px solid {GRAY_MID};
    border-top: none;
    border-radius: 0 0 10px 10px;
    padding: 16px;
  }}

  /* ---- Caption / footer ---- */
  .caption-text {{
    font-size: 12px;
    color: {GRAY_DIM};
    margin-top: 8px;
  }}
  .footer {{
    margin-top: 48px;
    padding-top: 24px;
    border-top: 1px solid {GRAY_MID};
    font-size: 12px;
    color: {GRAY_DIM};
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  /* ---- Hide default streamlit chrome ---- */
  #MainMenu, footer, header {{ visibility: hidden; }}
  .stDeployButton {{ display: none; }}
</style>
""", unsafe_allow_html=True)

# ── Constants ──────────────────────────────────────────────────────────────────
FORECAST_DIR  = Path(__file__).parent.parent / "output" / "forecasts"
CLOSURE_START = 1
CLOSURE_END   = 5

def latest_forecast_path(forecast_dir: Path) -> Path:
    files = list(forecast_dir.glob("9day_*.csv"))
    if not files:
        st.error(f"No forecast files found in {forecast_dir}")
        st.stop()
    def parse_dt(p):
        ts = p.stem.split("_", 1)[1]           # e.g. "110426-23.13"
        return datetime.strptime(ts, "%d%m%y-%H.%M")
    return max(files, key=parse_dt)

# ── Load data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_forecast(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path, parse_dates=["hour"])
    return df.sort_values("hour").reset_index(drop=True)

@st.cache_data
def daily_summary(df: pd.DataFrame) -> pd.DataFrame:
    # Service day: 05:00 on day D through 00:00 on day D+1 (hours 01–04 closed)
    svc = df[~df["hour"].dt.hour.between(CLOSURE_START, CLOSURE_END - 1)].copy()
    svc["service_day"] = (svc["hour"] - pd.Timedelta(hours=5)).dt.date

    # Drop service days where the forecast doesn't cover all 20 service hours
    counts = svc.groupby("service_day")["hour"].transform("count")
    svc = svc[counts == 20]

    daily = (
        svc.groupby("service_day")
        .agg(
            total_trips    =("predicted_trips",    "sum"),
            peak_trips_hr  =("predicted_trips",    "max"),
            avg_temp_c     =("temp_c",             "mean"),
            total_precip_mm=("precip_mm",          "sum"),
            avg_cloud_pct  =("cloud_area_fraction", "mean"),
        )
        .reset_index()
        .rename(columns={"service_day": "date"})
    )
    daily["is_rainy"] = daily["total_precip_mm"] > 1.0
    return daily

forecast_path = latest_forecast_path(FORECAST_DIR)
fetch_time    = datetime.strptime(forecast_path.stem.split("_", 1)[1], "%d%m%y-%H.%M") \
                        .replace(tzinfo=ZoneInfo("Europe/Oslo"))
age_hours     = (datetime.now(tz=timezone.utc) - fetch_time).total_seconds() / 3600

df    = load_forecast(forecast_path)
daily = daily_summary(df)
open_df = df[~df["hour"].dt.hour.between(CLOSURE_START, CLOSURE_END - 1)]

forecast_start = df["hour"].min()
forecast_end   = df["hour"].max()

# Computed KPIs
total_trips  = int(open_df["predicted_trips"].sum())
peak_hourly  = int(open_df["predicted_trips"].max())
peak_time    = open_df.loc[open_df["predicted_trips"].idxmax(), "hour"]
avg_temp     = df["temp_c"].mean()
total_precip = df["precip_mm"].sum()

# ── Hero header ────────────────────────────────────────────────────────────────
_logo_b64 = base64.b64encode((Path(__file__).parent / "BysykkelLogo.png").read_bytes()).decode()
logo_img  = f'<img src="data:image/png;base64,{_logo_b64}" width="34" height="34" style="display:block;">'

period_str = (
    f"{forecast_start.strftime('%-d %b')} – {forecast_end.strftime('%-d %b %Y')}"
)

age_minutes = age_hours * 60
if age_minutes < 1:
    age_label = "Updated just now"
elif age_hours < 1:
    age_label = f"Updated {age_minutes:.0f}m ago"
elif age_hours < 48:
    age_label = f"Updated {age_hours:.0f}h ago"
else:
    age_label = f"Updated {age_hours / 24:.0f}d ago"
age_pill_color = "#C0392B" if age_hours > 30 else BLUE

st.markdown(f"""
<div class="hero">
  <div class="hero-wordmark">
    <div class="hero-logo-ring">{logo_img}</div>
    <span class="hero-brand">Oslo Bysykkel</span>
  </div>
  <div class="hero-title">9-Day Forecast</div>
  <p class="hero-sub">
    Nine days of Oslo bicycle sharing, predicted to the hour.<br>
    Updated daily. Code and other details on <a href="https://github.com/DylanKreynen/BysykkelForecast" target="_blank" style="color:inherit; opacity:0.75;">GitHub</a>.
  </p>
  <span class="hero-pill">{period_str}</span>
  <span class="hero-pill" style="background:{age_pill_color}; margin-left:8px;">{age_label}</span>
</div>
""", unsafe_allow_html=True)

if age_hours > 30:
    st.warning(
        f"⚠️ Forecast is {age_hours:.0f} hours old. The daily update may have failed — "
        "check the GitHub Actions workflow.",
        icon=None,
    )

# ── KPI strip ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="kpi-grid">
  <div class="kpi-card">
    <div class="kpi-label">Total trips (next 9 days)</div>
    <div class="kpi-value kpi-accent">{total_trips:,}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Peak hourly trips</div>
    <div class="kpi-value">{peak_hourly:,}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Peak time</div>
    <div class="kpi-value" style="font-size:20px;">{peak_time.strftime("%a %-d %b, %H:%M")}</div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Avg temperature</div>
    <div class="kpi-value">{avg_temp:.1f}<span>°C</span></div>
  </div>
  <div class="kpi-card">
    <div class="kpi-label">Total precipitation</div>
    <div class="kpi-value">{total_precip:.1f}<span>mm</span></div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Helper: closure bands ──────────────────────────────────────────────────────
def add_closure_bands(fig, df, n_rows):
    dates = df["hour"].dt.normalize().unique()
    for i in range(1, n_rows + 1):
        yaxis_key = "yaxis" if i == 1 else f"yaxis{i}"
        y0, y1 = fig.layout[yaxis_key].domain
        for d in dates:
            fig.add_shape(
                type="rect",
                xref="x", yref="paper",
                x0=pd.Timestamp(d) + pd.Timedelta(hours=CLOSURE_START),
                x1=pd.Timestamp(d) + pd.Timedelta(hours=CLOSURE_END),
                y0=y0, y1=y1,
                fillcolor=NAVY, opacity=0.06, line_width=0,
            )

def chart_layout(fig, height):
    fig.update_layout(
        height=height,
        showlegend=False,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        margin=dict(l=0, r=12, t=32, b=36),
        hovermode="x unified",
        dragmode=False,
        hoverlabel=dict(
            bgcolor=NAVY,
            font_color=WHITE,
            font_family=FONT_STACK,
            font_size=13,
            bordercolor=NAVY,
        ),
        font=dict(family=FONT_STACK, color=NAVY),
    )
    fig.update_xaxes(
        showgrid=True, gridcolor=GRAY_MID, gridwidth=1,
        tickfont=dict(size=12, color=GRAY_DIM),
        tickformat="%a %-d %b\n%H:%M",
        zeroline=False,
    )
    fig.update_yaxes(
        showgrid=True, gridcolor=GRAY_MID, gridwidth=1,
        tickfont=dict(size=12, color=GRAY_DIM),
        zeroline=False,
    )

# ── Hourly forecast chart ──────────────────────────────────────────────────────
st.markdown('<div class="section-heading">Hourly forecast</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Hover to inspect individual hours. Grey bands mark the 01:00–04:59 service closure window.</div>',
    unsafe_allow_html=True,
)

with st.container():
    fig = make_subplots(
        rows=3, cols=1,
        shared_xaxes=True,
        row_heights=[0.50, 0.25, 0.25],
        vertical_spacing=0.04,
        subplot_titles=("Predicted trips / hour", "Temperature  (°C)", "Precipitation  (mm)"),
    )

    # Subplot title styling – keep Plotly's default centred position to avoid clipping
    for ann in fig.layout.annotations:
        ann.update(x=0, xanchor="left")
        ann.font.update(family=FONT_STACK, size=13, color=GRAY_DIM)

    # Trips
    fig.add_trace(
        go.Scatter(
            x=df["hour"], y=df["predicted_trips"],
            fill="tozeroy",
            fillcolor=f"rgba(0,95,201,0.12)",
            line=dict(color=BLUE, width=2),
            name="Trips",
            hovertemplate="<b>%{y:,} trips</b><extra></extra>",
        ),
        row=1, col=1,
    )
    add_closure_bands(fig, df, n_rows=3)

    # Temperature
    fig.add_trace(
        go.Scatter(
            x=df["hour"], y=df["temp_c"],
            line=dict(color=ORANGE, width=2),
            name="Temp",
            hovertemplate="<b>%{y:.1f} °C</b><extra></extra>",
        ),
        row=2, col=1,
    )
    fig.add_hline(
        y=0, line_dash="dot", line_color=GRAY_DIM, line_width=1,
        annotation_text="0°C",
        annotation_font=dict(size=11, color=GRAY_DIM, family=FONT_STACK),
        annotation_position="right",
        row=2, col=1,
    )

    # Precipitation
    fig.add_trace(
        go.Bar(
            x=df["hour"], y=df["precip_mm"],
            marker_color=PRECIP_BLUE,
            marker_line_width=0,
            name="Precip",
            hovertemplate="<b>%{y:.1f} mm</b><extra></extra>",
        ),
        row=3, col=1,
    )

    chart_layout(fig, height=560)

    # Shift date labels to noon so they sit centred under each day.
    # Only include noon ticks within the data range (the first day's noon may
    # fall before the forecast start when the run begins in the evening).
    x_min, x_max = df["hour"].min(), df["hour"].max()
    noon_ticks = [
        d + pd.Timedelta(hours=12)
        for d in pd.date_range(x_min.normalize(), x_max.normalize(), freq="D")
        if d + pd.Timedelta(hours=12) >= x_min
    ]
    fig.update_xaxes(
        tickvals=noon_ticks,
        ticktext=[
            t.strftime("%a %-d %b<br>%H:%M") if i == 0 else t.strftime("%a %-d %b")
            for i, t in enumerate(noon_ticks)
        ],
        range=[x_min, x_max],
        hoverformat="%H:%M %b %-d",
    )

    fig.update_yaxes(title_text="trips / hr", title_font=dict(size=11, color=GRAY_DIM), row=1, col=1)
    fig.update_yaxes(title_text="°C",         title_font=dict(size=11, color=GRAY_DIM), row=2, col=1)
    fig.update_yaxes(title_text="mm",         title_font=dict(size=11, color=GRAY_DIM),
                     rangemode="tozero",       row=3, col=1)

    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

# ── Daily summary ──────────────────────────────────────────────────────────────
st.markdown('<hr class="bysykkel-divider">', unsafe_allow_html=True)
st.markdown('<div class="section-heading">Daily summary</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-sub">Shows complete service days (05:00 am to 01:00 am next day) only. Lighter bars indicate rainy days (total precipitation > 1 mm).</div>',
    unsafe_allow_html=True,
)

col_bar, col_tbl = st.columns([3, 2], gap="large")

with col_bar:
    bar_colors = [
        f"rgba(0,95,201,0.35)" if r else BLUE
        for r in daily["is_rainy"]
    ]
    fig_d = go.Figure(
        go.Bar(
            x=[pd.Timestamp(d).strftime("%a<br>%-d %b") for d in daily["date"]],
            y=daily["total_trips"],
            marker_color=bar_colors,
            marker_line_width=0,
            text=daily["total_trips"].apply(lambda v: f"{v:,}"),
            textposition="outside",
            textfont=dict(family=FONT_STACK, size=12, color=NAVY),
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Total trips: <b>%{y:,}</b><br>"
                "Peak: %{customdata[0]:,}/hr<br>"
                "Avg temp: %{customdata[1]:.1f} °C<br>"
                "Precip: %{customdata[2]:.1f} mm<extra></extra>"
            ),
            customdata=daily[["peak_trips_hr","avg_temp_c","total_precip_mm"]].values,
        )
    )
    fig_d.update_layout(
        height=300,
        plot_bgcolor=WHITE,
        paper_bgcolor=WHITE,
        margin=dict(l=0, r=0, t=24, b=0),
        yaxis=dict(
            title="Total trips",
            title_font=dict(size=11, color=GRAY_DIM, family=FONT_STACK),
            showgrid=True, gridcolor=GRAY_MID,
            tickfont=dict(size=12, color=GRAY_DIM, family=FONT_STACK),
            zeroline=False,
        ),
        xaxis=dict(
            tickfont=dict(size=12, color=GRAY_DIM, family=FONT_STACK),
            zeroline=False,
        ),
        hoverlabel=dict(
            bgcolor=NAVY, font_color=WHITE,
            font_family=FONT_STACK, font_size=13,
            bordercolor=NAVY,
        ),
        font=dict(family=FONT_STACK, color=NAVY),
        dragmode=False,
    )
    st.plotly_chart(fig_d, use_container_width=True, config={"displayModeBar": False})

with col_tbl:
    tbl = daily[["date","total_trips","peak_trips_hr","avg_temp_c","total_precip_mm","avg_cloud_pct"]].copy()
    tbl.columns = ["Date", "Total trips", "Peak /hr", "Avg temp (°C)", "Precip (mm)", "Cloud (%)"]
    tbl["Date"]         = tbl["Date"].astype(str)
    tbl["Avg temp (°C)"]= tbl["Avg temp (°C)"].round(1)
    tbl["Precip (mm)"]  = tbl["Precip (mm)"].round(1)
    tbl["Cloud (%)"]    = tbl["Cloud (%)"].round(0).astype(int)
    st.dataframe(
        tbl,
        hide_index=True,
        use_container_width=True,
        column_config={
            "Total trips": st.column_config.NumberColumn(format="%d"),
            "Peak /hr":    st.column_config.NumberColumn(format="%d"),
        },
    )

# ── Wind & cloud detail (expander) ─────────────────────────────────────────────
st.markdown('<hr class="bysykkel-divider">', unsafe_allow_html=True)

with st.expander("Wind & cloud cover detail"):
    fig_wc = make_subplots(
        rows=2, cols=1,
        shared_xaxes=True,
        row_heights=[0.5, 0.5],
        vertical_spacing=0.08,
        subplot_titles=("Wind speed  (m/s)", "Cloud cover  (%)"),
    )
    for ann in fig_wc.layout.annotations:
        ann.update(x=0, xanchor="left")
        ann.font.update(family=FONT_STACK, size=13, color=GRAY_DIM)

    fig_wc.add_trace(
        go.Scatter(
            x=df["hour"], y=df["wind_speed_ms"],
            fill="tozeroy", fillcolor=f"rgba(45,163,94,0.12)",
            line=dict(color=GREEN, width=2),
            hovertemplate="<b>%{y:.1f} m/s</b><extra></extra>",
        ),
        row=1, col=1,
    )
    fig_wc.add_trace(
        go.Scatter(
            x=df["hour"], y=df["cloud_area_fraction"],
            fill="tozeroy", fillcolor=f"rgba(193,194,207,0.25)",
            line=dict(color=GRAY_DIM, width=2),
            hovertemplate="<b>%{y:.0f}%</b><extra></extra>",
        ),
        row=2, col=1,
    )
    chart_layout(fig_wc, height=360)
    add_closure_bands(fig_wc, df, n_rows=2)

    fig_wc.update_xaxes(
        tickvals=noon_ticks,
        ticktext=[
            t.strftime("%a %-d %b<br>%H:%M") if i == 0 else t.strftime("%a %-d %b")
            for i, t in enumerate(noon_ticks)
        ],
    )

    fig_wc.update_yaxes(title_text="m/s", title_font=dict(size=11, color=GRAY_DIM), rangemode="tozero", row=1)
    fig_wc.update_yaxes(title_text="%",   title_font=dict(size=11, color=GRAY_DIM), range=[0, 102],     row=2)
    st.plotly_chart(fig_wc, use_container_width=True, config={"displayModeBar": False})

# ── Raw data (expander) ────────────────────────────────────────────────────────
with st.expander("Raw hourly data"):
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True,
        column_config={
            "predicted_trips":    st.column_config.NumberColumn("Predicted trips", format="%d"),
            "temp_c":             st.column_config.NumberColumn("Temp (°C)",        format="%.1f"),
            "precip_mm":          st.column_config.NumberColumn("Precip (mm)",      format="%.1f"),
            "wind_speed_ms":      st.column_config.NumberColumn("Wind (m/s)",       format="%.1f"),
            "cloud_area_fraction":st.column_config.NumberColumn("Cloud (%)",        format="%.1f"),
        },
    )

# ── Disclaimer ─────────────────────────────────────────────────────────────────
st.markdown("""
<div style="
    margin-top: 48px;
    padding: 16px 20px;
    background: #EEF2F7;
    border-left: 4px solid #72718E;
    border-radius: 6px;
    font-size: 12px;
    color: #72718E;
    line-height: 1.6;
">
  <strong>Disclaimer</strong> &nbsp;·&nbsp;
  This is an independent hobby project and is <em>not</em> affiliated with, endorsed by,
  or in any way connected to Oslo Bysykkel or its operators.
  Trip forecasts are generated by a machine learning model trained on historical data
  and are provided for informational purposes only.
  No responsibility is taken for the accuracy, completeness, or timeliness of the forecasts.
  Use at your own discretion.
</div>
""", unsafe_allow_html=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="footer">
  <span>Weather data: <strong>MET Norway Locationforecast 2.0</strong> &nbsp;·&nbsp;
        Historical trip data: <strong>Oslo Bysykkel</strong> &nbsp;·&nbsp;
        Model: <strong>2x XGBoost</strong> &nbsp;·&nbsp;
        Forecast generated: <strong>{fetch_time.strftime("%-d %b %Y, %H:%M")} (Oslo time)</strong>
  </span>
  <span>© <a href="https://www.linkedin.com/in/dylan-kreynen" target="_blank" style="color:inherit;">Dylan Kreynen</a></span>
</div>
""", unsafe_allow_html=True)
