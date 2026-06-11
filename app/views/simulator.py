import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from model import predict_single
from theme import PLOTLY_LAYOUT, AIRBUS_COLORS

PRESETS = {
    "Paris CDG": dict(metar_temperature_c=11.0, metar_relative_humidity=78.0, metar_dew_point_c=7.0,
        metar_wind_speed_kn=9.0, metar_visibility_mi=6.0, metar_hour_precipitation=0.03,
        total_parking_minutes=30000, sea_salt_aerosol_05_5_mixing_ratio=3e-10,
        sulphur_dioxide_mass_mixing_ratio=1.5e-8, nitrogen_dioxide_mass_mixing_ratio=4e-8,
        sea_salt_aerosol_003_05_mixing_ratio=1e-11, sea_salt_aerosol_5_20_mixing_ratio=1e-11,
        dust_aerosol_003_055_mixing_ratio=5e-10, dust_aerosol_055_09_mixing_ratio=8e-10,
        dust_aerosol_09_20_mixing_ratio=1e-9),
    "Dubai DXB": dict(metar_temperature_c=36.0, metar_relative_humidity=45.0, metar_dew_point_c=22.0,
        metar_wind_speed_kn=12.0, metar_visibility_mi=3.0, metar_hour_precipitation=0.0,
        total_parking_minutes=25000, sea_salt_aerosol_05_5_mixing_ratio=8e-10,
        sulphur_dioxide_mass_mixing_ratio=2e-8, nitrogen_dioxide_mass_mixing_ratio=6e-8,
        sea_salt_aerosol_003_05_mixing_ratio=2e-11, sea_salt_aerosol_5_20_mixing_ratio=5e-11,
        dust_aerosol_003_055_mixing_ratio=2e-8, dust_aerosol_055_09_mixing_ratio=3e-8,
        dust_aerosol_09_20_mixing_ratio=4e-8),
    "Singapore SIN": dict(metar_temperature_c=28.0, metar_relative_humidity=84.0, metar_dew_point_c=24.5,
        metar_wind_speed_kn=6.0, metar_visibility_mi=5.0, metar_hour_precipitation=0.08,
        total_parking_minutes=28000, sea_salt_aerosol_05_5_mixing_ratio=1.5e-9,
        sulphur_dioxide_mass_mixing_ratio=1e-8, nitrogen_dioxide_mass_mixing_ratio=3e-8,
        sea_salt_aerosol_003_05_mixing_ratio=3e-11, sea_salt_aerosol_5_20_mixing_ratio=6e-11,
        dust_aerosol_003_055_mixing_ratio=4e-10, dust_aerosol_055_09_mixing_ratio=6e-10,
        dust_aerosol_09_20_mixing_ratio=8e-10),
    "New York JFK": dict(metar_temperature_c=13.0, metar_relative_humidity=65.0, metar_dew_point_c=6.0,
        metar_wind_speed_kn=14.0, metar_visibility_mi=7.0, metar_hour_precipitation=0.02,
        total_parking_minutes=32000, sea_salt_aerosol_05_5_mixing_ratio=5e-10,
        sulphur_dioxide_mass_mixing_ratio=2.5e-8, nitrogen_dioxide_mass_mixing_ratio=5e-8,
        sea_salt_aerosol_003_05_mixing_ratio=1.5e-11, sea_salt_aerosol_5_20_mixing_ratio=2e-11,
        dust_aerosol_003_055_mixing_ratio=8e-10, dust_aerosol_055_09_mixing_ratio=1e-9,
        dust_aerosol_09_20_mixing_ratio=1.5e-9),
}

DEFAULT_EXTRAS = dict(
    hydrophilic_organic_matter_aerosol_mixing_ratio=1e-7, hydrophobic_organic_matter_aerosol_mixing_ratio=8e-8,
    hydrophilic_black_carbon_aerosol_mixing_ratio=1e-9, hydrophobic_black_carbon_aerosol_mixing_ratio=2e-9,
    sulphate_aerosol_mixing_ratio=8e-9, ethane=5e-9, c3h8=2e-9, isoprene=8e-9,
    carbon_monoxide_mass_mixing_ratio=1e-6, ozone_mass_mixing_ratio=5e-8, h2o2=1e-9,
    formaldehyde=4e-9, hno3=4e-9, nitrogen_monoxide_mass_mixing_ratio=2e-8,
    oh=8e-14, organic_nitrates=1e-9, specific_humidity=0.01,
    temperature=290.0, metar_dew_point_c=10.0,
)


def show():
    st.markdown("""
    <div class="page-header">
        <h1>Simulateur de risque</h1>
        <p>Ajustez les conditions environnementales et observez le risque en temps réel</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("**Scénarios prédéfinis**")
    cols_p = st.columns(4)
    for i, name in enumerate(PRESETS):
        with cols_p[i]:
            if st.button(f"✈ {name}", use_container_width=True):
                st.session_state['preset'] = name

    preset_values = PRESETS.get(st.session_state.get('preset', 'Paris CDG'), PRESETS['Paris CDG'])
    st.markdown("---")

    left, right = st.columns(2)
    with left:
        st.markdown("**Conditions météorologiques**")
        temp     = st.slider("🌡️ Température (°C)", -20.0, 50.0, float(preset_values['metar_temperature_c']), 0.5)
        humidity = st.slider("💧 Humidité relative (%)", 0.0, 100.0, float(preset_values['metar_relative_humidity']), 1.0)
        precip   = st.slider("🌧️ Précipitations (mm/h)", 0.0, 0.5, float(preset_values['metar_hour_precipitation']), 0.01)
        parking  = st.slider("⏱️ Parking mensuel (min)", 1000, 44640, int(preset_values['total_parking_minutes']), 500)
        st.caption(f"→ {parking/44640*100:.0f}% du mois au sol")

    with right:
        st.markdown("**Exposition atmosphérique**")
        sea_salt = st.slider("🌊 Sel marin (×10⁻¹⁰)", 0.0, 20.0, float(preset_values['sea_salt_aerosol_05_5_mixing_ratio'])*1e10, 0.1)
        dust     = st.slider("🏜️ Poussière (×10⁻⁹)", 0.0, 50.0, float(preset_values['dust_aerosol_003_055_mixing_ratio'])*1e9, 0.5)
        so2      = st.slider("🏭 SO₂ (×10⁻⁸)", 0.0, 10.0, float(preset_values['sulphur_dioxide_mass_mixing_ratio'])*1e8, 0.1)
        no2      = st.slider("🚗 NO₂ (×10⁻⁸)", 0.0, 15.0, float(preset_values['nitrogen_dioxide_mass_mixing_ratio'])*1e8, 0.1)

    features = {**DEFAULT_EXTRAS, **preset_values, **{
        'metar_temperature_c': temp, 'metar_relative_humidity': humidity,
        'metar_hour_precipitation': precip, 'total_parking_minutes': parking,
        'sea_salt_aerosol_05_5_mixing_ratio': sea_salt * 1e-10,
        'sea_salt_aerosol_003_05_mixing_ratio': sea_salt * 0.1 * 1e-10,
        'sea_salt_aerosol_5_20_mixing_ratio': sea_salt * 0.05 * 1e-10,
        'dust_aerosol_003_055_mixing_ratio': dust * 1e-9,
        'dust_aerosol_055_09_mixing_ratio': dust * 1.5 * 1e-9,
        'dust_aerosol_09_20_mixing_ratio': dust * 2 * 1e-9,
        'sulphur_dioxide_mass_mixing_ratio': so2 * 1e-8,
        'nitrogen_dioxide_mass_mixing_ratio': no2 * 1e-8,
    }}

    risk_score = predict_single(features)
    gauge_color = AIRBUS_COLORS['red'] if risk_score > 0.7 else AIRBUS_COLORS['orange'] if risk_score > 0.4 else AIRBUS_COLORS['green']
    risk_label  = "RISQUE ÉLEVÉ" if risk_score > 0.7 else "RISQUE MODÉRÉ" if risk_score > 0.4 else "RISQUE FAIBLE"

    st.markdown("---")
    st.markdown("**Risque de corrosion prédit**")
    col_gauge, col_factors = st.columns([1, 2])

    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=risk_score * 100,
            title={'text': risk_label, 'font': {'color': gauge_color, 'size': 15}},
            number={'suffix': '%', 'font': {'color': AIRBUS_COLORS['navy'], 'size': 40}},
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color=gauge_color, thickness=0.25),
                bgcolor='rgba(0,0,0,0.03)',
                steps=[
                    dict(range=[0, 40],  color='rgba(0,170,85,0.1)'),
                    dict(range=[40, 70], color='rgba(255,165,0,0.1)'),
                    dict(range=[70, 100],color='rgba(204,34,34,0.1)'),
                ],
            ),
        ))
        fig_gauge.update_layout(**PLOTLY_LAYOUT, height=300)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with col_factors:
        st.markdown("**Principaux facteurs de risque**")
        factors = pd.DataFrame([
            ("Humidité",        humidity / 100),
            ("Temps au sol",    parking / 44640),
            ("Sel marin",       min(sea_salt / 20, 1)),
            ("SO₂",             min(so2 / 10, 1)),
            ("NO₂",             min(no2 / 15, 1)),
            ("Poussière",       min(dust / 50, 1)),
            ("Stress thermique",abs(temp - 15) / 35),
            ("Précipitations",  min(precip / 0.5, 1)),
        ], columns=['Facteur', 'Score']).sort_values('Score')

        fig_f = go.Figure(go.Bar(
            x=factors['Score'], y=factors['Facteur'], orientation='h',
            marker=dict(color=factors['Score'],
                        colorscale=[[0, AIRBUS_COLORS['green']], [0.5, AIRBUS_COLORS['orange']], [1, AIRBUS_COLORS['red']]]),
            text=[f"{v:.0%}" for v in factors['Score']],
            textposition='outside', textfont=dict(color=AIRBUS_COLORS['text'], size=12),
        ))
        fig_f.update_layout(**PLOTLY_LAYOUT, height=300, xaxis_range=[0, 1.25], xaxis_title="Sévérité")
        st.plotly_chart(fig_f, use_container_width=True)
