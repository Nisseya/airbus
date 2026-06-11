import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from model import get_predictions, get_fleet_summary
from theme import PLOTLY_LAYOUT, AIRBUS_COLORS


def show():
    fleet = get_fleet_summary()
    preds = get_predictions()

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
