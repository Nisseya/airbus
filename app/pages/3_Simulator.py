import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from model import predict_single, get_predictions
from theme import AIRBUS_CSS, PLOTLY_LAYOUT, AIRBUS_COLORS

st.set_page_config(page_title="Simulator | Airbus CRM", page_icon="🔬", layout="wide")
st.markdown(AIRBUS_CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="padding: 16px 0 24px 0; border-bottom: 1px solid rgba(0,130,200,0.2); margin-bottom: 16px;">
        <div style="font-size: 22px; font-weight: 800; letter-spacing: 0.1em; color: white;">✈ AIRBUS</div>
        <div style="font-size: 11px; color: rgba(255,255,255,0.4); font-weight: 500; letter-spacing: 0.08em; margin-top: 2px;">CORROSION RISK MONITOR</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("""
<div class="page-header">
    <h1>🔬 Risk Simulator</h1>
    <p>Adjust environmental conditions and observe corrosion risk in real time</p>
</div>
""", unsafe_allow_html=True)

# ─── Preset scenarios ──────────────────────────────────────────────────────────
PRESETS = {
    "Paris CDG": dict(
        metar_temperature_c=11.0, metar_relative_humidity=78.0, metar_dew_point_c=7.0,
        metar_wind_speed_kn=9.0, metar_visibility_mi=6.0, metar_hour_precipitation=0.03,
        total_parking_minutes=30000, sea_salt_aerosol_05_5_mixing_ratio=3e-10,
        sulphur_dioxide_mass_mixing_ratio=1.5e-8, nitrogen_dioxide_mass_mixing_ratio=4e-8,
        sea_salt_aerosol_003_05_mixing_ratio=1e-11, sea_salt_aerosol_5_20_mixing_ratio=1e-11,
        dust_aerosol_003_055_mixing_ratio=5e-10, dust_aerosol_055_09_mixing_ratio=8e-10,
        dust_aerosol_09_20_mixing_ratio=1e-9,
    ),
    "Dubai DXB": dict(
        metar_temperature_c=36.0, metar_relative_humidity=45.0, metar_dew_point_c=22.0,
        metar_wind_speed_kn=12.0, metar_visibility_mi=3.0, metar_hour_precipitation=0.0,
        total_parking_minutes=25000, sea_salt_aerosol_05_5_mixing_ratio=8e-10,
        sulphur_dioxide_mass_mixing_ratio=2e-8, nitrogen_dioxide_mass_mixing_ratio=6e-8,
        sea_salt_aerosol_003_05_mixing_ratio=2e-11, sea_salt_aerosol_5_20_mixing_ratio=5e-11,
        dust_aerosol_003_055_mixing_ratio=2e-8, dust_aerosol_055_09_mixing_ratio=3e-8,
        dust_aerosol_09_20_mixing_ratio=4e-8,
    ),
    "Singapore SIN": dict(
        metar_temperature_c=28.0, metar_relative_humidity=84.0, metar_dew_point_c=24.5,
        metar_wind_speed_kn=6.0, metar_visibility_mi=5.0, metar_hour_precipitation=0.08,
        total_parking_minutes=28000, sea_salt_aerosol_05_5_mixing_ratio=1.5e-9,
        sulphur_dioxide_mass_mixing_ratio=1e-8, nitrogen_dioxide_mass_mixing_ratio=3e-8,
        sea_salt_aerosol_003_05_mixing_ratio=3e-11, sea_salt_aerosol_5_20_mixing_ratio=6e-11,
        dust_aerosol_003_055_mixing_ratio=4e-10, dust_aerosol_055_09_mixing_ratio=6e-10,
        dust_aerosol_09_20_mixing_ratio=8e-10,
    ),
    "New York JFK": dict(
        metar_temperature_c=13.0, metar_relative_humidity=65.0, metar_dew_point_c=6.0,
        metar_wind_speed_kn=14.0, metar_visibility_mi=7.0, metar_hour_precipitation=0.02,
        total_parking_minutes=32000, sea_salt_aerosol_05_5_mixing_ratio=5e-10,
        sulphur_dioxide_mass_mixing_ratio=2.5e-8, nitrogen_dioxide_mass_mixing_ratio=5e-8,
        sea_salt_aerosol_003_05_mixing_ratio=1.5e-11, sea_salt_aerosol_5_20_mixing_ratio=2e-11,
        dust_aerosol_003_055_mixing_ratio=8e-10, dust_aerosol_055_09_mixing_ratio=1e-9,
        dust_aerosol_09_20_mixing_ratio=1.5e-9,
    ),
}

DEFAULT_EXTRAS = dict(
    metar_wind_speed_kn=8.0, metar_visibility_mi=5.0, metar_hour_precipitation=0.01,
    hydrophilic_organic_matter_aerosol_mixing_ratio=1e-7, hydrophobic_organic_matter_aerosol_mixing_ratio=8e-8,
    hydrophilic_black_carbon_aerosol_mixing_ratio=1e-9, hydrophobic_black_carbon_aerosol_mixing_ratio=2e-9,
    sulphate_aerosol_mixing_ratio=8e-9, ethane=5e-9, c3h8=2e-9, isoprene=8e-9,
    carbon_monoxide_mass_mixing_ratio=1e-6, ozone_mass_mixing_ratio=5e-8, h2o2=1e-9,
    formaldehyde=4e-9, hno3=4e-9, nitrogen_monoxide_mass_mixing_ratio=2e-8,
    oh=8e-14, organic_nitrates=1e-9, specific_humidity=0.01,
    temperature=290.0, metar_dew_point_c=10.0,
)

st.markdown("**Quick Scenario Presets**")
cols_preset = st.columns(4)
selected_preset = None
for i, (name, _) in enumerate(PRESETS.items()):
    with cols_preset[i]:
        if st.button(f"✈ {name}", use_container_width=True):
            selected_preset = name

if selected_preset:
    st.session_state['preset'] = selected_preset

preset_values = PRESETS.get(st.session_state.get('preset', 'Paris CDG'), PRESETS['Paris CDG'])

st.markdown("---")

# ─── Sliders ──────────────────────────────────────────────────────────────────
left, right = st.columns([1, 1])

with left:
    st.markdown("**Weather Conditions**")
    temp = st.slider("🌡️ Temperature (°C)", -20.0, 50.0, float(preset_values.get('metar_temperature_c', 15.0)), 0.5)
    humidity = st.slider("💧 Relative Humidity (%)", 0.0, 100.0, float(preset_values.get('metar_relative_humidity', 65.0)), 1.0)
    precip = st.slider("🌧️ Precipitation (mm/h)", 0.0, 0.5, float(preset_values.get('metar_hour_precipitation', 0.01)), 0.01)
    parking = st.slider("⏱️ Monthly Parking (min)", 1000, 44640, int(preset_values.get('total_parking_minutes', 30000)), 500)
    parking_pct = parking / 44640 * 100

    st.markdown(f"<p style='color:rgba(255,255,255,0.45); font-size:12px;'>→ {parking_pct:.0f}% of month on ground</p>", unsafe_allow_html=True)

with right:
    st.markdown("**Atmospheric Exposure**")
    sea_salt = st.slider("🌊 Sea Salt Aerosol (×10⁻¹⁰)", 0.0, 20.0,
                          float(preset_values.get('sea_salt_aerosol_05_5_mixing_ratio', 5e-10)) * 1e10, 0.1)
    dust = st.slider("🏜️ Dust Aerosol (×10⁻⁹)", 0.0, 50.0,
                      float(preset_values.get('dust_aerosol_003_055_mixing_ratio', 5e-10)) * 1e9, 0.5)
    so2 = st.slider("🏭 Sulphur Dioxide SO₂ (×10⁻⁸)", 0.0, 10.0,
                     float(preset_values.get('sulphur_dioxide_mass_mixing_ratio', 1e-8)) * 1e8, 0.1)
    no2 = st.slider("🚗 Nitrogen Dioxide NO₂ (×10⁻⁸)", 0.0, 15.0,
                     float(preset_values.get('nitrogen_dioxide_mass_mixing_ratio', 4e-8)) * 1e8, 0.1)

# ─── Build feature dict ────────────────────────────────────────────────────────
features = {**DEFAULT_EXTRAS, **preset_values}
features.update({
    'metar_temperature_c': temp,
    'metar_relative_humidity': humidity,
    'metar_hour_precipitation': precip,
    'total_parking_minutes': parking,
    'sea_salt_aerosol_05_5_mixing_ratio': sea_salt * 1e-10,
    'sea_salt_aerosol_003_05_mixing_ratio': sea_salt * 0.1 * 1e-10,
    'sea_salt_aerosol_5_20_mixing_ratio': sea_salt * 0.05 * 1e-10,
    'dust_aerosol_003_055_mixing_ratio': dust * 1e-9,
    'dust_aerosol_055_09_mixing_ratio': dust * 1.5 * 1e-9,
    'dust_aerosol_09_20_mixing_ratio': dust * 2 * 1e-9,
    'sulphur_dioxide_mass_mixing_ratio': so2 * 1e-8,
    'nitrogen_dioxide_mass_mixing_ratio': no2 * 1e-8,
})

risk_score = predict_single(features)

# ─── Risk gauge ────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("**Predicted Corrosion Risk**")

if risk_score > 0.7:
    gauge_color = AIRBUS_COLORS['red']
    risk_label = "HIGH RISK"
elif risk_score > 0.4:
    gauge_color = AIRBUS_COLORS['orange']
    risk_label = "MEDIUM RISK"
else:
    gauge_color = AIRBUS_COLORS['green']
    risk_label = "LOW RISK"

col_gauge, col_breakdown = st.columns([1, 2])

with col_gauge:
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number",
        value=risk_score * 100,
        title={'text': risk_label, 'font': {'color': gauge_color, 'size': 16, 'family': 'Inter'}},
        number={'suffix': '%', 'font': {'color': 'white', 'size': 40, 'family': 'Inter'}},
        gauge=dict(
            axis=dict(range=[0, 100], tickcolor='white', tickfont=dict(color='white')),
            bar=dict(color=gauge_color, thickness=0.25),
            bgcolor='rgba(255,255,255,0.05)',
            bordercolor='rgba(255,255,255,0.1)',
            steps=[
                dict(range=[0, 40], color='rgba(0,204,119,0.15)'),
                dict(range=[40, 70], color='rgba(255,165,0,0.15)'),
                dict(range=[70, 100], color='rgba(255,107,107,0.15)'),
            ],
            threshold=dict(line=dict(color=gauge_color, width=3), thickness=0.75, value=risk_score*100),
        ),
    ))
    fig_gauge.update_layout(**PLOTLY_LAYOUT, height=300)
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_breakdown:
    st.markdown("**Key Risk Drivers in this Scenario**")

    factors = [
        ("Humidity", humidity / 100),
        ("Parking time", parking / 44640),
        ("Sea salt", min(sea_salt / 20, 1)),
        ("SO₂", min(so2 / 10, 1)),
        ("NO₂", min(no2 / 15, 1)),
        ("Dust", min(dust / 50, 1)),
        ("Temperature stress", abs(temp - 15) / 35),
        ("Precipitation", min(precip / 0.5, 1)),
    ]
    factors_df = pd.DataFrame(factors, columns=['Factor', 'Score']).sort_values('Score', ascending=True)

    fig_factors = go.Figure(go.Bar(
        x=factors_df['Score'],
        y=factors_df['Factor'],
        orientation='h',
        marker=dict(
            color=factors_df['Score'],
            colorscale=[[0, AIRBUS_COLORS['green']], [0.5, AIRBUS_COLORS['orange']], [1, AIRBUS_COLORS['red']]],
        ),
        text=[f"{v:.0%}" for v in factors_df['Score']],
        textposition='outside',
        textfont=dict(color='white', size=12),
    ))
    fig_factors.update_layout(**PLOTLY_LAYOUT, height=300, xaxis_range=[0, 1.25],
                              xaxis_title="Relative severity", yaxis_title="")
    st.plotly_chart(fig_factors, use_container_width=True)
