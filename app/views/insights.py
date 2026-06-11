import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from model import get_feature_importance, get_predictions, get_fleet_summary
from theme import PLOTLY_LAYOUT, AIRBUS_COLORS


def show():
    preds   = get_predictions()
    fleet   = get_fleet_summary()
    importance = get_feature_importance()

    st.markdown("""
    <div class="page-header">
        <h1>Insights & Business Impact</h1>
        <p>Model explainability, risk drivers, and ROI analysis</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🧠 Model Explainability", "💶 ROI Calculator", "🌍 Environmental Profiling"])

    with tab1:
        col_fi, col_txt = st.columns([2, 1])
        with col_fi:
            st.markdown("**Top 15 Risk Factors (XGBoost Feature Importance)**")
            top15 = importance.head(15).sort_values('importance')
            colors = [AIRBUS_COLORS['red'] if i >= 12 else AIRBUS_COLORS['blue'] if i >= 8 else AIRBUS_COLORS['light_blue']
                      for i in range(len(top15))]
            fig_fi = go.Figure(go.Bar(
                x=top15['importance'], y=top15['label'], orientation='h',
                marker_color=colors,
                text=[f"{v:.4f}" for v in top15['importance']],
                textposition='outside', textfont=dict(color=AIRBUS_COLORS['text'], size=11),
            ))
            layout = {**PLOTLY_LAYOUT, 'margin': dict(l=200, r=60, t=40, b=16)}
            fig_fi.update_layout(**layout, height=500, xaxis_title="Importance score")
            st.plotly_chart(fig_fi, use_container_width=True)

        with col_txt:
            st.markdown("**Top 3 drivers**")
            for _, row in importance.head(3).iterrows():
                pct = row['importance'] / importance['importance'].sum() * 100
                st.markdown(f"""
                <div class="airbus-card">
                    <div style="font-size:12px; font-weight:700; color:{AIRBUS_COLORS['blue']};">{row['label']}</div>
                    <div style="font-size:26px; font-weight:800; color:{AIRBUS_COLORS['navy']};">{pct:.1f}%</div>
                    <div style="font-size:11px; color:{AIRBUS_COLORS['muted']};">of model decisions</div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        st.markdown("**Cost-Benefit Analysis**")
        col_p, col_r = st.columns(2)
        with col_p:
            fleet_size           = st.slider("Fleet size", 10, 500, 142, 5)
            inspection_cost      = st.slider("Inspection cost (€k)", 10, 200, 50, 5)
            repair_cost          = st.slider("Repair cost if missed (€k)", 100, 2000, 500, 50)
            detection_rate       = st.slider("Model detection rate (%)", 50, 99, 85, 1)
            false_positive_rate  = st.slider("False positive rate (%)", 1, 30, 10, 1)
            annual_corrosion_pct = st.slider("Annual corrosion incidence (%)", 1, 30, 8, 1)

        with col_r:
            n_corroded   = fleet_size * annual_corrosion_pct / 100
            n_detected   = n_corroded * detection_rate / 100
            n_missed     = n_corroded - n_detected
            n_fp         = fleet_size * false_positive_rate / 100
            cost_without = n_corroded * repair_cost * 1000
            cost_with    = n_missed * repair_cost * 1000 + (n_detected + n_fp) * inspection_cost * 1000
            savings      = cost_without - cost_with
            roi          = savings / max((n_detected + n_fp) * inspection_cost * 1000, 1)

            st.markdown(f"""
            <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;">
                <div class="airbus-card">
                    <div class="kpi-label">Without model</div>
                    <div class="kpi-value kpi-value-red">€{cost_without/1e6:.1f}M</div>
                    <div class="kpi-sub">Annual repair cost</div>
                </div>
                <div class="airbus-card">
                    <div class="kpi-label">With model</div>
                    <div class="kpi-value kpi-value-blue">€{cost_with/1e6:.1f}M</div>
                    <div class="kpi-sub">Inspections + missed</div>
                </div>
                <div class="airbus-card">
                    <div class="kpi-label">Annual savings</div>
                    <div class="kpi-value kpi-value-green">€{savings/1e6:.1f}M</div>
                    <div class="kpi-sub">Net reduction</div>
                </div>
                <div class="airbus-card">
                    <div class="kpi-label">ROI</div>
                    <div class="kpi-value kpi-value-blue">{roi:.1f}x</div>
                    <div class="kpi-sub">Return on investment</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            fig_roi = go.Figure(go.Bar(
                x=['No Model', 'With Model'],
                y=[cost_without/1e6, cost_with/1e6],
                marker_color=[AIRBUS_COLORS['red'], AIRBUS_COLORS['green']],
                text=[f"€{v:.2f}M" for v in [cost_without/1e6, cost_with/1e6]],
                textposition='outside', textfont=dict(color=AIRBUS_COLORS['text'], size=14),
            ))
            fig_roi.update_layout(**PLOTLY_LAYOUT, height=240, showlegend=False, yaxis_title="Cost (€M)")
            st.plotly_chart(fig_roi, use_container_width=True)

    with tab3:
        PROFILE_COLS = ['metar_temperature_c', 'metar_relative_humidity',
                        'sea_salt_aerosol_05_5_mixing_ratio', 'dust_aerosol_003_055_mixing_ratio',
                        'sulphur_dioxide_mass_mixing_ratio', 'nitrogen_dioxide_mass_mixing_ratio',
                        'total_parking_minutes']
        profile = preds.groupby('aircraft_id')[PROFILE_COLS].mean().reset_index()
        profile = profile.merge(fleet[['aircraft_id', 'max_risk', 'risk_level']], on='aircraft_id')
        color_map = {'High': AIRBUS_COLORS['red'], 'Medium': AIRBUS_COLORS['orange'], 'Low': AIRBUS_COLORS['green']}

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Temperature vs. Humidity**")
            fig1 = px.scatter(profile, x='metar_temperature_c', y='metar_relative_humidity',
                              color='risk_level', color_discrete_map=color_map,
                              size='max_risk', size_max=16, hover_name='aircraft_id',
                              labels={'metar_temperature_c': 'Avg Temp (°C)', 'metar_relative_humidity': 'Avg Humidity (%)'})
            fig1.update_layout(**PLOTLY_LAYOUT, height=320)
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            st.markdown("**Sea Salt vs. SO₂**")
            fig2 = px.scatter(profile, x='sea_salt_aerosol_05_5_mixing_ratio', y='sulphur_dioxide_mass_mixing_ratio',
                              color='risk_level', color_discrete_map=color_map,
                              size='max_risk', size_max=16, hover_name='aircraft_id',
                              labels={'sea_salt_aerosol_05_5_mixing_ratio': 'Sea Salt', 'sulphur_dioxide_mass_mixing_ratio': 'SO₂'})
            fig2.update_layout(**PLOTLY_LAYOUT, height=320)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**Avg conditions by risk level**")
        summary = profile.groupby('risk_level')[PROFILE_COLS].mean().round(4)
        summary.columns = ['Temp (°C)', 'Humidity (%)', 'Sea Salt', 'Dust', 'SO₂', 'NO₂', 'Parking (min)']
        st.dataframe(summary, use_container_width=True)
