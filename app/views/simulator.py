import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from model import predict_single, get_predictions, get_fleet_summary
from theme import PLOTLY_LAYOUT, AIRBUS_COLORS


@st.cache_data
def _data_ranges(preds):
    q01 = preds.quantile(0.01)
    q99 = preds.quantile(0.99)
    return q01, q99


def show():
    preds = get_predictions()
    fleet = get_fleet_summary()

    st.markdown("""
    <div class="page-header">
        <h1>Simulateur de risque</h1>
        <p>Sélectionnez un appareil réel et modifiez ses conditions pour observer l'impact sur le risque</p>
    </div>
    """, unsafe_allow_html=True)

    sorted_ids = fleet.sort_values('max_risk', ascending=False)['aircraft_id'].tolist()

    col_a, col_m = st.columns(2)
    with col_a:
        aircraft_id = st.selectbox(
            "Appareil",
            sorted_ids,
            format_func=lambda x: f"{x}  —  Pic : {fleet.loc[fleet.aircraft_id==x,'max_risk'].values[0]:.3f}",
        )
    with col_m:
        ac_rows = preds[preds['aircraft_id'] == aircraft_id].sort_values('year_month')
        month_options = ac_rows['year_month'].tolist()
        year_month = st.selectbox("Mois d'observation", month_options)

    row = ac_rows[ac_rows['year_month'] == year_month].iloc[0]

    q01, q99 = _data_ranges(
        preds[['metar_temperature_c', 'metar_relative_humidity', 'metar_hour_precipitation',
               'total_parking_minutes', 'sea_salt_aerosol_05_5_mixing_ratio',
               'dust_aerosol_003_055_mixing_ratio', 'sulphur_dioxide_mass_mixing_ratio',
               'nitrogen_dioxide_mass_mixing_ratio']]
    )

    st.markdown("---")
    left, right = st.columns(2)

    with left:
        st.markdown("**Conditions météorologiques**")
        temp = st.slider(
            "🌡️ Température (°C)",
            float(q01['metar_temperature_c']), float(q99['metar_temperature_c']),
            float(row['metar_temperature_c']), 0.5,
        )
        humidity = st.slider(
            "💧 Humidité relative (%)",
            float(q01['metar_relative_humidity']), float(q99['metar_relative_humidity']),
            float(row['metar_relative_humidity']), 1.0,
        )
        precip = st.slider(
            "🌧️ Précipitations (mm/h)",
            0.0, float(q99['metar_hour_precipitation']),
            float(row['metar_hour_precipitation']), 0.001,
        )
        parking = st.slider(
            "⏱️ Parking mensuel (min)",
            int(q01['total_parking_minutes']), 44640,
            int(row['total_parking_minutes']), 500,
        )
        st.caption(f"→ {parking/44640*100:.0f}% du mois au sol")

    with right:
        st.markdown("**Exposition atmosphérique**")
        sea_salt = st.slider(
            "🌊 Sel marin (×10⁻¹⁰)",
            0.0, float(q99['sea_salt_aerosol_05_5_mixing_ratio']) * 1e10,
            float(row['sea_salt_aerosol_05_5_mixing_ratio']) * 1e10, 0.01,
        )
        dust = st.slider(
            "🏜️ Poussière (×10⁻⁹)",
            0.0, float(q99['dust_aerosol_003_055_mixing_ratio']) * 1e9,
            float(row['dust_aerosol_003_055_mixing_ratio']) * 1e9, 0.01,
        )
        so2 = st.slider(
            "🏭 SO₂ (×10⁻⁸)",
            0.0, float(q99['sulphur_dioxide_mass_mixing_ratio']) * 1e8,
            float(row['sulphur_dioxide_mass_mixing_ratio']) * 1e8, 0.01,
        )
        no2 = st.slider(
            "🚗 NO₂ (×10⁻⁸)",
            0.0, float(q99['nitrogen_dioxide_mass_mixing_ratio']) * 1e8,
            float(row['nitrogen_dioxide_mass_mixing_ratio']) * 1e8, 0.01,
        )

    features = row.drop(['aircraft_id', 'year_month', 'month_start_date', 'corrosion_risk', 'id'],
                        errors='ignore').to_dict()
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
    gauge_color = AIRBUS_COLORS['red'] if risk_score > 0.7 else AIRBUS_COLORS['orange'] if risk_score > 0.4 else AIRBUS_COLORS['green']
    risk_label  = "RISQUE ÉLEVÉ" if risk_score > 0.7 else "RISQUE MODÉRÉ" if risk_score > 0.4 else "RISQUE FAIBLE"

    original_risk = float(row['corrosion_risk'])
    delta = risk_score - original_risk

    st.markdown("---")
    st.markdown("**Risque de corrosion prédit**")
    col_gauge, col_factors = st.columns([1, 2])

    with col_gauge:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=risk_score * 100,
            delta={'reference': original_risk * 100, 'valueformat': '.1f', 'suffix': '%',
                   'increasing': {'color': AIRBUS_COLORS['red']},
                   'decreasing': {'color': AIRBUS_COLORS['green']}},
            title={'text': risk_label, 'font': {'color': gauge_color, 'size': 15}},
            number={'suffix': '%', 'font': {'color': AIRBUS_COLORS['navy'], 'size': 40}},
            gauge=dict(
                axis=dict(range=[0, 100]),
                bar=dict(color=gauge_color, thickness=0.25),
                bgcolor='rgba(0,0,0,0.03)',
                steps=[
                    dict(range=[0, 40],  color='rgba(0,170,85,0.1)'),
                    dict(range=[40, 70], color='rgba(255,165,0,0.1)'),
                    dict(range=[70, 100], color='rgba(204,34,34,0.1)'),
                ],
                threshold=dict(line=dict(color=AIRBUS_COLORS['navy'], width=2),
                               thickness=0.75, value=original_risk * 100),
            ),
        ))
        fig_gauge.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig_gauge, use_container_width=True)
        st.caption(f"Risque réel enregistré : **{original_risk:.3f}** | Variation : **{delta:+.3f}**")

    with col_factors:
        st.markdown("**Principaux facteurs de risque**")
        factors = pd.DataFrame([
            ("Humidité",         humidity / 100),
            ("Temps au sol",     parking / 44640),
            ("Sel marin",        min(sea_salt / (float(q99['sea_salt_aerosol_05_5_mixing_ratio']) * 1e10 + 1e-12), 1)),
            ("SO₂",              min(so2 / (float(q99['sulphur_dioxide_mass_mixing_ratio']) * 1e8 + 1e-12), 1)),
            ("NO₂",              min(no2 / (float(q99['nitrogen_dioxide_mass_mixing_ratio']) * 1e8 + 1e-12), 1)),
            ("Poussière",        min(dust / (float(q99['dust_aerosol_003_055_mixing_ratio']) * 1e9 + 1e-12), 1)),
            ("Stress thermique", abs(temp - 15) / 35),
            ("Précipitations",   min(precip / (float(q99['metar_hour_precipitation']) + 1e-12), 1)),
        ], columns=['Facteur', 'Score']).sort_values('Score')

        fig_f = go.Figure(go.Bar(
            x=factors['Score'], y=factors['Facteur'], orientation='h',
            marker=dict(color=factors['Score'],
                        colorscale=[[0, AIRBUS_COLORS['green']], [0.5, AIRBUS_COLORS['orange']], [1, AIRBUS_COLORS['red']]]),
            text=[f"{v:.0%}" for v in factors['Score']],
            textposition='outside', textfont=dict(color=AIRBUS_COLORS['text'], size=12),
        ))
        fig_f.update_layout(**PLOTLY_LAYOUT, height=320, xaxis_range=[0, 1.25], xaxis_title="Sévérité relative")
        st.plotly_chart(fig_f, use_container_width=True)
