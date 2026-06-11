import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from model import get_predictions, get_fleet_summary, get_corrosion_events
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
    col_tl, col_dist = st.columns(2)

    with col_tl:
        st.markdown("**Chronologie des événements de corrosion**")
        year_palette = {
            yr: c for yr, c in zip(
                sorted(cor['year'].unique()),
                [AIRBUS_COLORS['navy'], '#1a5276', '#1f618d', AIRBUS_COLORS['blue'],
                 '#2e86c1', '#3498db', '#5dade2', '#85c1e9',
                 AIRBUS_COLORS['orange'], AIRBUS_COLORS['red'], '#c0392b']
            )
        }
        fig_tl = go.Figure()
        for yr, grp in cor.groupby('year'):
            fig_tl.add_trace(go.Scatter(
                x=grp['observation_date'], y=grp['aircraft_id'],
                mode='markers',
                name=str(yr),
                marker=dict(color=year_palette.get(yr, AIRBUS_COLORS['blue']),
                            size=7, opacity=0.85, line=dict(width=0.5, color='white')),
                customdata=grp[['aircraft_delivery_year']].values,
                hovertemplate=(
                    "<b>Appareil %{y}</b><br>"
                    "Date corrosion : %{x|%d/%m/%Y}<br>"
                    "Livraison : %{customdata[0]}"
                    "<extra></extra>"
                ),
            ))
        layout_tl = {
            **PLOTLY_LAYOUT,
            'height': 420,
            'xaxis_title': "Date de corrosion",
            'yaxis': dict(title="Appareil", tickfont=dict(size=9), gridcolor='#e8eef4', color='#6b7e9a'),
            'legend_title': "Année",
        }
        fig_tl.update_layout(**layout_tl)
        st.plotly_chart(fig_tl, use_container_width=True)
        st.caption(f"{len(cor)} événements de corrosion — {cor['year'].min()}–{cor['year'].max()}")

    with col_dist:
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
