import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from model import get_feature_importance, get_predictions, get_fleet_summary, get_discriminant_factors
from theme import PLOTLY_LAYOUT, AIRBUS_COLORS


def show():
    preds      = get_predictions()
    fleet      = get_fleet_summary()
    importance = get_feature_importance()

    st.markdown("""
    <div class="page-header">
        <h1>Analyse & Impact business</h1>
        <p>Explicabilité du modèle, facteurs de risque et analyse ROI</p>
    </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3, tab4 = st.tabs(["🧠 Explicabilité du modèle", "💶 Calculateur ROI", "🌍 Profil environnemental", "🔍 Facteurs discriminants"])

    with tab1:
        col_fi, col_txt = st.columns([2, 1])
        with col_fi:
            st.markdown("**Top 15 facteurs de risque — Feature Importance (XGBoost)**")
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
            fig_fi.update_layout(**layout, height=500, xaxis_title="Score d'importance")
            st.plotly_chart(fig_fi, use_container_width=True)

        with col_txt:
            st.markdown("**Top 3 facteurs**")
            for _, row in importance.head(3).iterrows():
                pct = row['importance'] / importance['importance'].sum() * 100
                st.markdown(f"""
                <div class="airbus-card">
                    <div style="font-size:12px; font-weight:700; color:{AIRBUS_COLORS['blue']};">{row['label']}</div>
                    <div style="font-size:26px; font-weight:800; color:{AIRBUS_COLORS['navy']};">{pct:.1f}%</div>
                    <div style="font-size:11px; color:{AIRBUS_COLORS['muted']};">des décisions du modèle</div>
                </div>
                """, unsafe_allow_html=True)

    with tab2:
        st.markdown("**Analyse coût-bénéfice**")
        col_p, col_r = st.columns(2)
        with col_p:
            st.markdown("*Ajustez les paramètres pour modéliser votre scénario*")
            fleet_size           = st.slider("Taille de la flotte", 10, 500, 142, 5)
            inspection_cost      = st.slider("Coût par inspection (€k)", 10, 200, 50, 5)
            repair_cost          = st.slider("Coût réparation non détectée (€k)", 100, 2000, 500, 50)
            detection_rate       = st.slider("Taux de détection du modèle (%)", 50, 99, 85, 1)
            false_positive_rate  = st.slider("Taux de faux positifs (%)", 1, 30, 10, 1)
            annual_corrosion_pct = st.slider("Incidence annuelle de corrosion (%)", 1, 30, 8, 1)

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
                    <div class="kpi-label">Sans modèle</div>
                    <div class="kpi-value kpi-value-red">€{cost_without/1e6:.1f}M</div>
                    <div class="kpi-sub">Coût annuel de réparation</div>
                </div>
                <div class="airbus-card">
                    <div class="kpi-label">Avec modèle</div>
                    <div class="kpi-value kpi-value-blue">€{cost_with/1e6:.1f}M</div>
                    <div class="kpi-sub">Inspections + non détectés</div>
                </div>
                <div class="airbus-card">
                    <div class="kpi-label">Économies annuelles</div>
                    <div class="kpi-value kpi-value-green">€{savings/1e6:.1f}M</div>
                    <div class="kpi-sub">Réduction nette des coûts</div>
                </div>
                <div class="airbus-card">
                    <div class="kpi-label">ROI</div>
                    <div class="kpi-value kpi-value-blue">{roi:.1f}x</div>
                    <div class="kpi-sub">Retour sur investissement</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            fig_roi = go.Figure(go.Bar(
                x=['Sans modèle', 'Avec modèle'],
                y=[cost_without/1e6, cost_with/1e6],
                marker_color=[AIRBUS_COLORS['red'], AIRBUS_COLORS['green']],
                text=[f"€{v:.2f}M" for v in [cost_without/1e6, cost_with/1e6]],
                textposition='outside', textfont=dict(color=AIRBUS_COLORS['text'], size=14),
            ))
            fig_roi.update_layout(**PLOTLY_LAYOUT, height=240, showlegend=False, yaxis_title="Coût annuel (€M)")
            st.plotly_chart(fig_roi, use_container_width=True)

    with tab3:
        st.markdown("**Profil environnemental de la flotte**")
        st.caption("Appareils regroupés selon leur exposition environnementale moyenne")

        PROFILE_COLS = ['metar_temperature_c', 'metar_relative_humidity',
                        'sea_salt_aerosol_05_5_mixing_ratio', 'dust_aerosol_003_055_mixing_ratio',
                        'sulphur_dioxide_mass_mixing_ratio', 'nitrogen_dioxide_mass_mixing_ratio',
                        'total_parking_minutes']
        profile = preds.groupby('aircraft_id')[PROFILE_COLS].mean().reset_index()
        profile = profile.merge(fleet[['aircraft_id', 'max_risk', 'risk_level']], on='aircraft_id')
        profile['Niveau'] = profile['risk_level'].map({'High': 'Élevé', 'Medium': 'Modéré', 'Low': 'Faible'})
        color_map = {'Élevé': AIRBUS_COLORS['red'], 'Modéré': AIRBUS_COLORS['orange'], 'Faible': AIRBUS_COLORS['green']}

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Température vs. Humidité**")
            fig1 = px.scatter(profile, x='metar_temperature_c', y='metar_relative_humidity',
                              color='Niveau', color_discrete_map=color_map,
                              size='max_risk', size_max=16, hover_name='aircraft_id',
                              labels={'metar_temperature_c': 'Temp. moy. (°C)', 'metar_relative_humidity': 'Humidité moy. (%)'})
            fig1.update_layout(**PLOTLY_LAYOUT, height=320)
            st.plotly_chart(fig1, use_container_width=True)

        with c2:
            st.markdown("**Sel marin vs. SO₂**")
            fig2 = px.scatter(profile, x='sea_salt_aerosol_05_5_mixing_ratio', y='sulphur_dioxide_mass_mixing_ratio',
                              color='Niveau', color_discrete_map=color_map,
                              size='max_risk', size_max=16, hover_name='aircraft_id',
                              labels={'sea_salt_aerosol_05_5_mixing_ratio': 'Sel marin', 'sulphur_dioxide_mass_mixing_ratio': 'SO₂'})
            fig2.update_layout(**PLOTLY_LAYOUT, height=320)
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown("**Conditions moyennes par niveau de risque**")
        summary = profile.groupby('Niveau')[PROFILE_COLS].mean().round(4)
        summary.columns = ['Temp. (°C)', 'Humidité (%)', 'Sel marin', 'Poussière', 'SO₂', 'NO₂', 'Parking (min)']
        st.dataframe(summary, use_container_width=True)

    with tab4:
        st.markdown("**Facteurs discriminants — Corrosion précoce vs tardive**")
        st.caption(
            "Écart à la moyenne de la flotte (en écarts-types) pour les avions ayant corrodé tôt vs tard dans leur vie. "
            "La médiane est ~72 mois après livraison."
        )

        disc = get_discriminant_factors(n=15)

        COLOR_PRE  = '#B85450'
        COLOR_TARD = '#6C8EBF'

        fig_disc = go.Figure()
        fig_disc.add_trace(go.Bar(
            x=disc['précoce'], y=disc['label'],
            orientation='h', name='Corrosion précoce',
            marker_color=COLOR_PRE, opacity=0.85,
            hovertemplate='<b>%{y}</b><br>Précoce : %{x:.3f} σ<extra></extra>',
        ))
        fig_disc.add_trace(go.Bar(
            x=disc['tardive'], y=disc['label'],
            orientation='h', name='Corrosion tardive',
            marker_color=COLOR_TARD, opacity=0.85,
            hovertemplate='<b>%{y}</b><br>Tardive : %{x:.3f} σ<extra></extra>',
        ))
        fig_disc.add_vline(x=0, line_dash='dash', line_color='#333333', line_width=1.5)
        layout_disc = {
            **PLOTLY_LAYOUT,
            'legend': dict(orientation='h', y=1.04, x=1, xanchor='right', bgcolor='rgba(0,0,0,0)'),
            'margin': dict(l=180, r=40, t=50, b=40),
        }
        fig_disc.update_layout(
            **layout_disc,
            height=520,
            barmode='group',
            xaxis_title="Écart à la référence (en écarts-types)",
        )
        st.plotly_chart(fig_disc, use_container_width=True)

        col_a, col_b = st.columns(2)
        with col_a:
            top_pre = disc.sort_values('précoce', ascending=False).iloc[0]
            st.markdown(f"""
            <div class="airbus-card">
                <div style="font-size:12px; font-weight:700; color:{COLOR_PRE};">Principal marqueur précoce</div>
                <div style="font-size:20px; font-weight:800; color:{AIRBUS_COLORS['navy']};">{top_pre['label']}</div>
                <div style="font-size:13px; color:{AIRBUS_COLORS['muted']};">+{top_pre['précoce']:.2f} σ vs flotte</div>
            </div>
            """, unsafe_allow_html=True)
        with col_b:
            top_tard = disc.sort_values('tardive', ascending=False).iloc[0]
            st.markdown(f"""
            <div class="airbus-card">
                <div style="font-size:12px; font-weight:700; color:{COLOR_TARD};">Principal marqueur tardif</div>
                <div style="font-size:20px; font-weight:800; color:{AIRBUS_COLORS['navy']};">{top_tard['label']}</div>
                <div style="font-size:13px; color:{AIRBUS_COLORS['muted']};">+{top_tard['tardive']:.2f} σ vs flotte</div>
            </div>
            """, unsafe_allow_html=True)
