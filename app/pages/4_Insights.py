import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from model import get_feature_importance, get_predictions, get_fleet_summary
from theme import AIRBUS_CSS, PLOTLY_LAYOUT, AIRBUS_COLORS

st.markdown("""
<div class="page-header">
    <h1>📊 Insights & Business Impact</h1>
    <p>Model explainability, risk drivers, and ROI analysis</p>
</div>
""", unsafe_allow_html=True)

preds = get_predictions()
fleet = get_fleet_summary()
importance = get_feature_importance()

tab1, tab2, tab3 = st.tabs(["🧠 Model Explainability", "💶 ROI Calculator", "🌍 Environmental Profiling"])

# ─── Tab 1: Feature Importance ────────────────────────────────────────────────
with tab1:
    col_fi, col_text = st.columns([2, 1])

    with col_fi:
        st.markdown("**Top 15 Risk Factors — Feature Importance (XGBoost)**")
        top15 = importance.head(15).sort_values('importance')
        colors = [AIRBUS_COLORS['red'] if i >= 12 else AIRBUS_COLORS['blue'] if i >= 8 else AIRBUS_COLORS['light_blue']
                  for i in range(len(top15))]

        fig_fi = go.Figure(go.Bar(
            x=top15['importance'],
            y=top15['label'],
            orientation='h',
            marker_color=colors,
            text=[f"{v:.4f}" for v in top15['importance']],
            textposition='outside',
            textfont=dict(color='white', size=11),
        ))
        fig_fi.update_layout(**PLOTLY_LAYOUT, height=500,
                             xaxis_title="Feature importance score",
                             margin=dict(l=200, r=60, t=40, b=16))
        st.plotly_chart(fig_fi, use_container_width=True)

    with col_text:
        st.markdown("**Interpretation**")

        top3 = importance.head(3)
        for _, row in top3.iterrows():
            pct = row['importance'] / importance['importance'].sum() * 100
            st.markdown(f"""
            <div class="airbus-card" style="margin-bottom:12px;">
                <div style="font-size:13px; font-weight:700; color:#0082C8;">{row['label']}</div>
                <div style="font-size:22px; font-weight:800; color:white; margin: 4px 0;">{pct:.1f}%</div>
                <div style="font-size:11px; color:rgba(255,255,255,0.45);">of model decisions</div>
            </div>
            """, unsafe_allow_html=True)

        top_name = top3.iloc[0]['label']
        st.markdown(f"""
        <div style="margin-top:16px; padding:16px; background:rgba(0,130,200,0.08); border-radius:10px; border-left:3px solid #0082C8;">
            <p style="color:rgba(255,255,255,0.8); font-size:13px; margin:0;">
            <b>Key finding:</b> <b style="color:#0082C8;">{top_name}</b> is the strongest predictor of corrosion.
            Aircraft exposed to high levels of this factor should be prioritized for inspection.
            </p>
        </div>
        """, unsafe_allow_html=True)

# ─── Tab 2: ROI Calculator ────────────────────────────────────────────────────
with tab2:
    st.markdown("**Cost-Benefit Analysis**")

    col_params, col_results = st.columns([1, 1])

    with col_params:
        st.markdown("*Adjust parameters to model your scenario*")
        fleet_size = st.slider("Fleet size (aircraft)", 10, 500, 142, 5)
        inspection_cost = st.slider("Cost per inspection (€k)", 10, 200, 50, 5)
        repair_cost = st.slider("Cost per undetected corrosion repair (€k)", 100, 2000, 500, 50)
        detection_rate = st.slider("Model detection rate (%)", 50, 99, 85, 1)
        false_positive_rate = st.slider("False positive rate (%)", 1, 30, 10, 1)
        annual_corrosion_rate = st.slider("Annual corrosion incidence (%)", 1, 30, 8, 1)

    with col_results:
        n_corroded = fleet_size * annual_corrosion_rate / 100
        n_detected = n_corroded * detection_rate / 100
        n_missed = n_corroded - n_detected
        n_false_positives = fleet_size * false_positive_rate / 100

        cost_without_model = n_corroded * repair_cost * 1000
        cost_with_model = (n_missed * repair_cost * 1000) + \
                          ((n_detected + n_false_positives) * inspection_cost * 1000)
        savings = cost_without_model - cost_with_model
        roi = savings / (n_detected + n_false_positives) / inspection_cost / 1000 * 100

        st.markdown(f"""
        <div style="display:grid; grid-template-columns:1fr 1fr; gap:12px; margin-bottom:16px;">
            <div class="airbus-card">
                <div class="kpi-label">Without model</div>
                <div class="kpi-value kpi-value-red">€{cost_without_model/1e6:.1f}M</div>
                <div class="kpi-sub">Annual repair cost</div>
            </div>
            <div class="airbus-card">
                <div class="kpi-label">With model</div>
                <div class="kpi-value kpi-value-blue">€{cost_with_model/1e6:.1f}M</div>
                <div class="kpi-sub">Inspections + missed repairs</div>
            </div>
            <div class="airbus-card">
                <div class="kpi-label">Annual savings</div>
                <div class="kpi-value kpi-value-green">€{savings/1e6:.1f}M</div>
                <div class="kpi-sub">Net cost reduction</div>
            </div>
            <div class="airbus-card">
                <div class="kpi-label">ROI</div>
                <div class="kpi-value kpi-value-blue">{roi:.0f}x</div>
                <div class="kpi-sub">Return on inspection investment</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        breakdown = pd.DataFrame({
            'Scenario': ['No Model', 'With Model'],
            'Cost (€M)': [cost_without_model / 1e6, cost_with_model / 1e6],
        })
        fig_roi = go.Figure(go.Bar(
            x=breakdown['Scenario'], y=breakdown['Cost (€M)'],
            marker_color=[AIRBUS_COLORS['red'], AIRBUS_COLORS['green']],
            text=[f"€{v:.2f}M" for v in breakdown['Cost (€M)']],
            textposition='outside',
            textfont=dict(color='white', size=14),
        ))
        fig_roi.update_layout(**PLOTLY_LAYOUT, height=250, showlegend=False,
                              yaxis_title="Annual cost (€M)")
        st.plotly_chart(fig_roi, use_container_width=True)

# ─── Tab 3: Environmental Profiling ───────────────────────────────────────────
with tab3:
    st.markdown("**Fleet Environmental Profiling**")
    st.markdown("<p style='color:rgba(255,255,255,0.45); font-size:13px;'>Aircraft clustered by their average environmental exposure</p>", unsafe_allow_html=True)

    PROFILE_COLS = ['metar_temperature_c', 'metar_relative_humidity',
                    'sea_salt_aerosol_05_5_mixing_ratio', 'dust_aerosol_003_055_mixing_ratio',
                    'sulphur_dioxide_mass_mixing_ratio', 'nitrogen_dioxide_mass_mixing_ratio',
                    'total_parking_minutes']

    profile = preds.groupby('aircraft_id')[PROFILE_COLS].mean().reset_index()
    profile_merged = profile.merge(fleet[['aircraft_id', 'max_risk', 'risk_level']], on='aircraft_id')

    col_p1, col_p2 = st.columns(2)

    with col_p1:
        st.markdown("**Temperature vs. Humidity (by risk level)**")
        fig_env = px.scatter(
            profile_merged,
            x='metar_temperature_c', y='metar_relative_humidity',
            color='risk_level',
            color_discrete_map={'High': AIRBUS_COLORS['red'], 'Medium': AIRBUS_COLORS['orange'], 'Low': AIRBUS_COLORS['green']},
            size='max_risk', size_max=16,
            hover_name='aircraft_id',
            labels={'metar_temperature_c': 'Avg Temperature (°C)', 'metar_relative_humidity': 'Avg Humidity (%)'},
        )
        fig_env.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig_env, use_container_width=True)

    with col_p2:
        st.markdown("**Sea Salt vs. SO₂ (corrosion drivers)**")
        fig_chem = px.scatter(
            profile_merged,
            x='sea_salt_aerosol_05_5_mixing_ratio',
            y='sulphur_dioxide_mass_mixing_ratio',
            color='risk_level',
            color_discrete_map={'High': AIRBUS_COLORS['red'], 'Medium': AIRBUS_COLORS['orange'], 'Low': AIRBUS_COLORS['green']},
            size='max_risk', size_max=16,
            hover_name='aircraft_id',
            labels={
                'sea_salt_aerosol_05_5_mixing_ratio': 'Avg Sea Salt',
                'sulphur_dioxide_mass_mixing_ratio': 'Avg SO₂',
            },
        )
        fig_chem.update_layout(**PLOTLY_LAYOUT, height=320)
        st.plotly_chart(fig_chem, use_container_width=True)

    st.markdown("**Average environmental conditions by risk level**")
    summary = profile_merged.groupby('risk_level')[PROFILE_COLS].mean().round(4)
    summary.columns = ['Avg Temp (°C)', 'Avg Humidity (%)', 'Sea Salt', 'Dust', 'SO₂', 'NO₂', 'Parking (min)']
    st.dataframe(summary, use_container_width=True)
