import streamlit as st
import plotly.graph_objects as go
from model import get_predictions, get_fleet_summary
from theme import PLOTLY_LAYOUT, AIRBUS_COLORS

LABELS = {
    'metar_temperature_c': 'Température (°C)', 'metar_relative_humidity': 'Humidité relative (%)',
    'metar_dew_point_c': 'Point de rosée (°C)', 'metar_wind_speed_kn': 'Vent (kn)',
    'metar_hour_precipitation': 'Précipitations', 'total_parking_minutes': 'Temps parking (min)',
    'sea_salt_aerosol_003_05_mixing_ratio': 'Sel marin (fin)', 'sea_salt_aerosol_05_5_mixing_ratio': 'Sel marin (moyen)',
    'sea_salt_aerosol_5_20_mixing_ratio': 'Sel marin (grossier)', 'dust_aerosol_003_055_mixing_ratio': 'Poussière (fin)',
    'dust_aerosol_055_09_mixing_ratio': 'Poussière (moyen)', 'sulphate_aerosol_mixing_ratio': 'Sulfate',
    'hydrophilic_black_carbon_aerosol_mixing_ratio': 'Carbone noir',
    'sulphur_dioxide_mass_mixing_ratio': 'SO₂', 'nitrogen_dioxide_mass_mixing_ratio': 'NO₂',
    'nitrogen_monoxide_mass_mixing_ratio': 'NO', 'ozone_mass_mixing_ratio': 'Ozone',
    'carbon_monoxide_mass_mixing_ratio': 'CO', 'formaldehyde': 'Formaldéhyde', 'hno3': 'HNO₃',
}

ENV_GROUPS = {
    "🌡️ Météo": ['metar_temperature_c', 'metar_relative_humidity', 'metar_dew_point_c',
                 'metar_wind_speed_kn', 'metar_hour_precipitation', 'total_parking_minutes'],
    "🧪 Aérosols": ['sea_salt_aerosol_003_05_mixing_ratio', 'sea_salt_aerosol_05_5_mixing_ratio',
                   'sea_salt_aerosol_5_20_mixing_ratio', 'dust_aerosol_003_055_mixing_ratio',
                   'dust_aerosol_055_09_mixing_ratio', 'sulphate_aerosol_mixing_ratio',
                   'hydrophilic_black_carbon_aerosol_mixing_ratio'],
    "☁️ Polluants": ['sulphur_dioxide_mass_mixing_ratio', 'nitrogen_dioxide_mass_mixing_ratio',
                    'nitrogen_monoxide_mass_mixing_ratio', 'ozone_mass_mixing_ratio',
                    'carbon_monoxide_mass_mixing_ratio', 'formaldehyde', 'hno3'],
}


def show():
    preds = get_predictions()
    fleet = get_fleet_summary()
    sorted_ids = fleet.sort_values('max_risk', ascending=False)['aircraft_id'].tolist()

    st.markdown("""
    <div class="page-header">
        <h1>Détail appareil</h1>
        <p>Historique de risque individuel et profil environnemental</p>
    </div>
    """, unsafe_allow_html=True)

    col_sel, col_cmp = st.columns([2, 1])
    with col_sel:
        aircraft_id = st.selectbox("Sélectionner un appareil", sorted_ids,
            format_func=lambda x: f"{x}  —  Pic : {fleet.loc[fleet.aircraft_id==x,'max_risk'].values[0]:.3f}")
    with col_cmp:
        compare_id = st.selectbox("Comparer avec (optionnel)", ['Aucun'] + sorted_ids)

    ac_data = preds[preds['aircraft_id'] == aircraft_id].sort_values('year_month').copy()
    ac_fleet = fleet[fleet['aircraft_id'] == aircraft_id].iloc[0]
    risk_color = (AIRBUS_COLORS['red'] if ac_fleet['max_risk'] > 0.7
                  else AIRBUS_COLORS['orange'] if ac_fleet['max_risk'] > 0.4
                  else AIRBUS_COLORS['green'])

    k1, k2, k3, k4 = st.columns(4)
    with k1: st.metric("Identifiant", aircraft_id)
    with k2: st.metric("Risque max", f"{ac_fleet['max_risk']:.3f}")
    with k3: st.metric("Risque moyen", f"{ac_fleet['mean_risk']:.3f}")
    with k4: st.metric("Mois suivis", int(ac_fleet['months']))

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("**Évolution du risque de corrosion**")

    r, g, b = int(risk_color[1:3], 16), int(risk_color[3:5], 16), int(risk_color[5:], 16)
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=ac_data['year_month'], y=ac_data['corrosion_risk'],
        mode='lines+markers', fill='tozeroy',
        line=dict(color=risk_color, width=2.5),
        fillcolor=f"rgba({r},{g},{b},0.08)",
        name=aircraft_id, marker=dict(size=5),
    ))
    if compare_id != 'Aucun':
        cmp = preds[preds['aircraft_id'] == compare_id].sort_values('year_month')
        fig.add_trace(go.Scatter(
            x=cmp['year_month'], y=cmp['corrosion_risk'],
            mode='lines+markers', line=dict(color=AIRBUS_COLORS['blue'], width=2, dash='dash'),
            name=compare_id, marker=dict(size=4),
        ))
    fig.add_hline(y=0.7, line_dash='dot', line_color=AIRBUS_COLORS['red'], opacity=0.6,
                  annotation_text="Seuil risque élevé (0.70)", annotation_font_color=AIRBUS_COLORS['red'])
    fig.add_hline(y=0.4, line_dash='dot', line_color=AIRBUS_COLORS['orange'], opacity=0.4)
    fig.update_layout(**PLOTLY_LAYOUT, height=340, xaxis_title="Mois",
                      yaxis_title="Risque de corrosion", yaxis_range=[0, 1.05])
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    tabs = st.tabs(list(ENV_GROUPS.keys()))
    for tab, (group_name, cols) in zip(tabs, ENV_GROUPS.items()):
        with tab:
            available = [c for c in cols if c in ac_data.columns]
            fig_env = go.Figure()
            for col in available:
                if ac_data[col].std() == 0:
                    continue
                norm = (ac_data[col] - ac_data[col].min()) / (ac_data[col].max() - ac_data[col].min() + 1e-12)
                fig_env.add_trace(go.Scatter(
                    x=ac_data['year_month'], y=norm,
                    mode='lines', name=LABELS.get(col, col), line=dict(width=1.8),
                ))
            fig_env.update_layout(**PLOTLY_LAYOUT, height=300,
                                  yaxis_title="Valeur normalisée (0–1)", xaxis_title="Mois")
            st.plotly_chart(fig_env, use_container_width=True)
