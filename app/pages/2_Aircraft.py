import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from model import get_predictions, get_fleet_summary
from theme import AIRBUS_CSS, PLOTLY_LAYOUT, AIRBUS_COLORS

st.markdown("""
<div class="page-header">
    <h1>✈️ Aircraft Detail</h1>
    <p>Individual corrosion risk timeline and environmental profile</p>
</div>
""", unsafe_allow_html=True)

preds = get_predictions()
fleet = get_fleet_summary()

# Sort aircraft by max_risk descending for the selector
sorted_ids = fleet.sort_values('max_risk', ascending=False)['aircraft_id'].tolist()

col_sel, col_compare = st.columns([2, 1])
with col_sel:
    aircraft_id = st.selectbox("Select Aircraft", sorted_ids,
                                format_func=lambda x: f"{x}  —  Peak risk: {fleet.loc[fleet.aircraft_id==x,'max_risk'].values[0]:.3f}")
with col_compare:
    compare_id = st.selectbox("Compare with (optional)", ['None'] + sorted_ids)

# ─── Aircraft data ─────────────────────────────────────────────────────────────
ac_data = preds[preds['aircraft_id'] == aircraft_id].sort_values('year_month').copy()
ac_fleet = fleet[fleet['aircraft_id'] == aircraft_id].iloc[0]

risk_color = AIRBUS_COLORS['red'] if ac_fleet['max_risk'] > 0.7 else \
             AIRBUS_COLORS['orange'] if ac_fleet['max_risk'] > 0.4 else AIRBUS_COLORS['green']
risk_label = ac_fleet['risk_level']

# ─── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
with k1:
    st.metric("Aircraft ID", aircraft_id)
with k2:
    st.metric("Peak Risk", f"{ac_fleet['max_risk']:.3f}")
with k3:
    st.metric("Avg Risk", f"{ac_fleet['mean_risk']:.3f}")
with k4:
    st.metric("Months Tracked", int(ac_fleet['months']))

st.markdown("<br>", unsafe_allow_html=True)

# ─── Risk timeline ─────────────────────────────────────────────────────────────
st.markdown("**Corrosion Risk Timeline**")

fig_timeline = go.Figure()

fig_timeline.add_trace(go.Scatter(
    x=ac_data['year_month'], y=ac_data['corrosion_risk'],
    mode='lines+markers',
    fill='tozeroy',
    line=dict(color=risk_color, width=2.5),
    fillcolor=f"rgba({int(risk_color[1:3],16)},{int(risk_color[3:5],16)},{int(risk_color[5:],16)},0.1)",
    name=aircraft_id,
    marker=dict(size=5),
))

if compare_id != 'None':
    cmp_data = preds[preds['aircraft_id'] == compare_id].sort_values('year_month')
    fig_timeline.add_trace(go.Scatter(
        x=cmp_data['year_month'], y=cmp_data['corrosion_risk'],
        mode='lines+markers',
        line=dict(color=AIRBUS_COLORS['light_blue'], width=2, dash='dash'),
        name=compare_id,
        marker=dict(size=4),
    ))

fig_timeline.add_hline(y=0.7, line_dash='dot', line_color=AIRBUS_COLORS['red'], opacity=0.6,
                        annotation_text="High risk threshold (0.70)", annotation_font_color=AIRBUS_COLORS['red'])
fig_timeline.add_hline(y=0.4, line_dash='dot', line_color=AIRBUS_COLORS['orange'], opacity=0.4)

fig_timeline.update_layout(**PLOTLY_LAYOUT, height=340,
                            xaxis_title="Month", yaxis_title="Corrosion Risk",
                            yaxis_range=[0, 1.05])
st.plotly_chart(fig_timeline, use_container_width=True)

# ─── Environmental breakdown ───────────────────────────────────────────────────
st.markdown("---")
tab1, tab2, tab3 = st.tabs(["🌡️ Weather", "🧪 Aerosols", "☁️ Pollutants"])

ENV_GROUPS = {
    "Weather": ['metar_temperature_c', 'metar_relative_humidity', 'metar_dew_point_c',
                'metar_wind_speed_kn', 'metar_hour_precipitation', 'total_parking_minutes'],
    "Aerosols": ['sea_salt_aerosol_003_05_mixing_ratio', 'sea_salt_aerosol_05_5_mixing_ratio',
                 'sea_salt_aerosol_5_20_mixing_ratio', 'dust_aerosol_003_055_mixing_ratio',
                 'dust_aerosol_055_09_mixing_ratio', 'sulphate_aerosol_mixing_ratio',
                 'hydrophilic_black_carbon_aerosol_mixing_ratio'],
    "Pollutants": ['sulphur_dioxide_mass_mixing_ratio', 'nitrogen_dioxide_mass_mixing_ratio',
                   'nitrogen_monoxide_mass_mixing_ratio', 'ozone_mass_mixing_ratio',
                   'carbon_monoxide_mass_mixing_ratio', 'formaldehyde', 'hno3'],
}

LABELS = {
    'metar_temperature_c': 'Temperature (°C)',
    'metar_relative_humidity': 'Humidity (%)',
    'metar_dew_point_c': 'Dew Point (°C)',
    'metar_wind_speed_kn': 'Wind (kn)',
    'metar_hour_precipitation': 'Precipitation',
    'total_parking_minutes': 'Parking (min)',
    'sea_salt_aerosol_003_05_mixing_ratio': 'Sea Salt (fine)',
    'sea_salt_aerosol_05_5_mixing_ratio': 'Sea Salt (med)',
    'sea_salt_aerosol_5_20_mixing_ratio': 'Sea Salt (coarse)',
    'dust_aerosol_003_055_mixing_ratio': 'Dust (fine)',
    'dust_aerosol_055_09_mixing_ratio': 'Dust (med)',
    'sulphate_aerosol_mixing_ratio': 'Sulphate',
    'hydrophilic_black_carbon_aerosol_mixing_ratio': 'Black Carbon',
    'sulphur_dioxide_mass_mixing_ratio': 'SO₂',
    'nitrogen_dioxide_mass_mixing_ratio': 'NO₂',
    'nitrogen_monoxide_mass_mixing_ratio': 'NO',
    'ozone_mass_mixing_ratio': 'Ozone',
    'carbon_monoxide_mass_mixing_ratio': 'CO',
    'formaldehyde': 'Formaldehyde',
    'hno3': 'HNO₃',
}

def plot_env_group(cols, title):
    available = [c for c in cols if c in ac_data.columns]
    if not available:
        return
    fig = go.Figure()
    for col in available:
        if ac_data[col].std() == 0:
            continue
        normalized = (ac_data[col] - ac_data[col].min()) / (ac_data[col].max() - ac_data[col].min() + 1e-12)
        fig.add_trace(go.Scatter(
            x=ac_data['year_month'], y=normalized,
            mode='lines', name=LABELS.get(col, col),
            line=dict(width=1.8),
        ))
    fig.update_layout(**PLOTLY_LAYOUT, height=300,
                      yaxis_title="Normalized value (0–1)",
                      xaxis_title="Month")
    st.plotly_chart(fig, use_container_width=True)

with tab1:
    plot_env_group(ENV_GROUPS['Weather'], "Weather")

with tab2:
    plot_env_group(ENV_GROUPS['Aerosols'], "Aerosols")

with tab3:
    plot_env_group(ENV_GROUPS['Pollutants'], "Pollutants")
