import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from model import (get_predictions, get_fleet_summary, get_corrosion_events,
                   get_corrosion_age_exposure, get_partial_correlations)
from theme import PLOTLY_LAYOUT, AIRBUS_COLORS


def show():
    fleet    = get_fleet_summary()
    preds    = get_predictions()
    cor      = get_corrosion_events()

    st.markdown("""
    <div class="page-header">
        <h1>Vue d'ensemble de la flotte</h1>
        <p>Surveillance en temps réel du risque de corrosion — flotte test 2014</p>
    </div>
    """, unsafe_allow_html=True)

    total = len(fleet)
    high_risk = (fleet['risk_level'] == 'High').sum()
    avg_risk = fleet['mean_risk'].mean()
    est_savings = high_risk * 450_000

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Appareils total", f"{total}")
    with c2:
        st.metric("Risque élevé", f"{high_risk}", delta=f"{high_risk/total*100:.0f}% de la flotte", delta_color="inverse")
    with c3:
        st.metric("Score de risque moyen", f"{avg_risk:.2f}")
    with c4:
        st.metric("Coût estimé à risque", f"€{est_savings/1e6:.1f}M")

    st.markdown("<br>", unsafe_allow_html=True)

    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("**Répartition des risques**")
        counts = fleet['risk_level'].value_counts()
        labels_fr = {'High': 'Élevé', 'Medium': 'Modéré', 'Low': 'Faible'}
        fig_donut = go.Figure(go.Pie(
            labels=[labels_fr.get(l, l) for l in counts.index.tolist()],
            values=counts.values.tolist(),
            hole=0.65,
            marker_colors=[AIRBUS_COLORS['red'], AIRBUS_COLORS['orange'], AIRBUS_COLORS['green']],
            textinfo='label+percent',
            textfont=dict(color=AIRBUS_COLORS['text'], size=13),
        ))
        fig_donut.add_annotation(
            text=f"<b>{total}</b><br><span style='font-size:11px'>Appareils</span>",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=18, color=AIRBUS_COLORS['text']),
        )
        fig_donut.update_layout(**PLOTLY_LAYOUT, height=300, showlegend=True)
        st.plotly_chart(fig_donut, use_container_width=True)

    with col_right:
        st.markdown("**Évolution du risque de la flotte**")
        monthly_avg = preds.groupby('year_month')['corrosion_risk'].mean().reset_index()
        monthly_avg = monthly_avg.sort_values('year_month')
        fig_line = go.Figure()
        fig_line.add_trace(go.Scatter(
            x=monthly_avg['year_month'], y=monthly_avg['corrosion_risk'],
            mode='lines', fill='tozeroy',
            line=dict(color=AIRBUS_COLORS['blue'], width=2.5),
            fillcolor='rgba(0,130,200,0.12)', name='Risque moyen',
        ))
        fig_line.add_hline(y=0.5, line_dash='dot', line_color=AIRBUS_COLORS['orange'],
                           annotation_text="Seuil (0.5)", annotation_font_color=AIRBUS_COLORS['orange'])
        fig_line.update_layout(**PLOTLY_LAYOUT, height=300,
                               xaxis_title="Mois", yaxis_title="Risque de corrosion", yaxis_range=[0, 1])
        st.plotly_chart(fig_line, use_container_width=True)

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Distribution des scores de risque**")
        fig_hist = px.histogram(fleet, x='max_risk', nbins=25,
                                color_discrete_sequence=[AIRBUS_COLORS['blue']],
                                labels={'max_risk': 'Risque maximal'})
        fig_hist.add_vline(x=0.7, line_dash='dot', line_color=AIRBUS_COLORS['red'],
                           annotation_text="Seuil risque élevé", annotation_font_color=AIRBUS_COLORS['red'])
        fig_hist.update_layout(**PLOTLY_LAYOUT, height=280, bargap=0.05, showlegend=False)
        st.plotly_chart(fig_hist, use_container_width=True)

    with col_b:
        st.markdown("**Top 10 — Appareils les plus à risque**")
        top10 = fleet.nlargest(10, 'max_risk')
        fig_bar = go.Figure(go.Bar(
            x=top10['max_risk'], y=top10['aircraft_id'], orientation='h',
            marker=dict(
                color=top10['max_risk'],
                colorscale=[[0, AIRBUS_COLORS['blue']], [0.5, AIRBUS_COLORS['orange']], [1, AIRBUS_COLORS['red']]],
                showscale=False,
            ),
            text=[f"{v:.2f}" for v in top10['max_risk']],
            textposition='outside', textfont=dict(color=AIRBUS_COLORS['text']),
        ))
        fig_bar.update_layout(**PLOTLY_LAYOUT, height=280,
                              xaxis_title="Score de risque maximal", xaxis_range=[0, 1.15])
        st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")
    st.markdown("**🔴 Appareils à risque élevé — Action requise**")
    high_df = fleet[fleet['risk_level'] == 'High'].sort_values('max_risk', ascending=False).copy()
    high_df['Risque max'] = (high_df['max_risk'] * 100).round(1).astype(str) + '%'
    high_df['Risque moyen'] = (high_df['mean_risk'] * 100).round(1).astype(str) + '%'
    high_df = high_df.rename(columns={'aircraft_id': 'Appareil', 'months': 'Mois suivis', 'last_month': 'Dernier relevé'})
    st.dataframe(high_df[['Appareil', 'Risque max', 'Risque moyen', 'Mois suivis', 'Dernier relevé']],
                 use_container_width=True, hide_index=True)

    st.markdown("---")
    st.markdown("**Distribution des observations environnementales par année**")
    preds['year'] = preds['year_month'].str[:4].astype(int)
    obs_year = preds.groupby('year').size().reset_index(name='observations')
    cor_year = cor.groupby('year').size().reset_index(name='corrosions')

    fig_dist = go.Figure()
    fig_dist.add_trace(go.Bar(
        x=obs_year['year'], y=obs_year['observations'],
        name='Observations', marker_color=AIRBUS_COLORS['blue'],
        opacity=0.85,
        hovertemplate="Année %{x}<br>Observations : %{y}<extra></extra>",
    ))
    fig_dist.add_trace(go.Bar(
        x=cor_year['year'], y=cor_year['corrosions'],
        name='Corrosions', marker_color=AIRBUS_COLORS['red'],
        opacity=0.9, yaxis='y2',
        hovertemplate="Année %{x}<br>Corrosions : %{y}<extra></extra>",
    ))
    fig_dist.update_layout(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,32,91,0.02)',
        font=dict(color='#1a2e4a', family='Inter'),
        height=380, barmode='group',
        xaxis_title="Année",
        legend=dict(orientation='h', y=1.08, x=0, bgcolor='rgba(0,0,0,0)'),
        margin=dict(l=16, r=16, t=40, b=16),
    )
    fig_dist.layout.yaxis.update(
        title=dict(text="Nb observations"),
        gridcolor='#e8eef4', color=AIRBUS_COLORS['blue'],
    )
    fig_dist.layout.yaxis2 = go.layout.YAxis(
        title=dict(text="Nb corrosions"),
        overlaying='y', side='right',
        showgrid=False, color=AIRBUS_COLORS['red'],
    )
    st.plotly_chart(fig_dist, use_container_width=True)
    st.caption("Axe gauche : observations environnementales mensuelles · Axe droit : cas de corrosion détectés")

    st.markdown("---")
    st.markdown("**🔬 Facteurs de corrosion précoce — analyse exploratoire**")

    age_expo = get_corrosion_age_exposure()
    pcorr = get_partial_correlations()

    st.caption(
        f"Sur les {len(age_expo)} appareils corrodés du jeu d'entraînement (âge médian au premier "
        f"constat : {age_expo['age_y'].median():.1f} ans), quelles expositions sont liées à une "
        "corrosion plus précoce, une fois neutralisés les facteurs connus "
        "(sel marin, humidité, temps au sol) ?"
    )

    col_pc, col_dec = st.columns([3, 2])

    with col_pc:
        st.markdown("**Effet indépendant de chaque exposition sur l'âge au 1er constat**")
        signif = pcorr[pcorr['t'].abs() >= 2].sort_values('r_partial', ascending=False)
        bar_colors = [AIRBUS_COLORS['red'] if r < 0 else AIRBUS_COLORS['green']
                      for r in signif['r_partial']]
        fig_pc = go.Figure(go.Bar(
            x=signif['r_partial'], y=signif['label'], orientation='h',
            marker_color=bar_colors,
            text=[f"{v:+.2f}" for v in signif['r_partial']],
            textposition='outside', textfont=dict(color=AIRBUS_COLORS['text'], size=11),
        ))
        layout_pc = {**PLOTLY_LAYOUT, 'margin': dict(l=170, r=50, t=16, b=16)}
        fig_pc.update_layout(**layout_pc, height=400,
                             xaxis_title="Corrélation partielle avec l'âge au 1er constat")
        st.plotly_chart(fig_pc, use_container_width=True)
        st.caption(
            "Effets significatifs uniquement (|t| ≥ 2). 🔴 Négatif = avance la corrosion, "
            "indépendamment du sel, de l'humidité et du parking · 🟢 Positif = la retarde. "
            "Le vent et le sel grossier (particules 5–20 µm, retombée très locale) dominent : "
            "à concentration de sel égale, le vent accélère le dépôt sur la cellule."
        )

    with col_dec:
        st.markdown("**Extrêmes d'exposition : corrosion combien plus tôt ?**")
        DECILE_FACTORS = [
            ('metar_wind_speed_kn', 'Vent'),
            ('sea_salt_aerosol_5_20_mixing_ratio', 'Sel marin (grossier)'),
            ('ozone_mass_mixing_ratio', 'Ozone'),
        ]
        names, age_lo, age_hi = [], [], []
        for col, name in DECILE_FACTORS:
            lo = age_expo[age_expo[col] <= age_expo[col].quantile(0.1)]['age_y'].median()
            hi = age_expo[age_expo[col] >= age_expo[col].quantile(0.9)]['age_y'].median()
            names.append(name); age_lo.append(lo); age_hi.append(hi)

        fig_dec = go.Figure()
        fig_dec.add_trace(go.Bar(
            x=names, y=age_lo, name='10% les moins exposés',
            marker_color=AIRBUS_COLORS['blue'],
            text=[f"{v:.1f}" for v in age_lo], textposition='outside',
            textfont=dict(color=AIRBUS_COLORS['text']),
        ))
        fig_dec.add_trace(go.Bar(
            x=names, y=age_hi, name='10% les plus exposés',
            marker_color=AIRBUS_COLORS['red'],
            text=[f"{v:.1f}" for v in age_hi], textposition='outside',
            textfont=dict(color=AIRBUS_COLORS['text']),
        ))
        fig_dec.update_layout(**PLOTLY_LAYOUT, height=400, barmode='group',
                              yaxis_title="Âge médian au 1er constat (ans)")
        st.plotly_chart(fig_dec, use_container_width=True)
        delta_salt = (age_lo[1] - age_hi[1]) * 12
        delta_wind = (age_lo[0] - age_hi[0]) * 12
        st.caption(
            f"Les 10 % d'appareils les plus exposés au sel grossier corrodent "
            f"~{delta_salt:.0f} mois plus tôt que les moins exposés ; "
            f"pour le vent l'écart est de ~{delta_wind:.0f} mois. "
            "Lecture : c'est l'aéroport « les pieds dans l'eau » et venteux qui tue, "
            "pas le sel diffus régional."
        )
