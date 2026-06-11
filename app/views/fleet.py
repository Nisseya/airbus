import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from model import get_fleet_summary, get_predictions
from theme import PLOTLY_LAYOUT, AIRBUS_COLORS


def show():
    fleet = get_fleet_summary()

    st.markdown("""
    <div class="page-header">
        <h1>Gestion de la flotte</h1>
        <p>Inventaire complet des appareils avec évaluation du risque de corrosion</p>
    </div>
    """, unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        risk_filter = st.multiselect("Niveau de risque", ['High', 'Medium', 'Low'],
                                     default=['High', 'Medium', 'Low'],
                                     format_func=lambda x: {'High': 'Élevé', 'Medium': 'Modéré', 'Low': 'Faible'}[x])
    with col_f2:
        sort_by = st.selectbox("Trier par", ['max_risk', 'mean_risk', 'months'], format_func=lambda x: {
            'max_risk': 'Risque max', 'mean_risk': 'Risque moyen', 'months': 'Mois suivis'}[x])
    with col_f3:
        min_risk = st.slider("Risque min.", 0.0, 1.0, 0.0, 0.05)

    filtered = fleet[
        fleet['risk_level'].isin(risk_filter) & (fleet['max_risk'] >= min_risk)
    ].sort_values(sort_by, ascending=False)

    st.caption(f"{len(filtered)} appareil(s) affiché(s) sur {len(fleet)}")

    st.markdown("**Profil de risque — Pic vs. Moyenne**")
    color_map = {'High': AIRBUS_COLORS['red'], 'Medium': AIRBUS_COLORS['orange'], 'Low': AIRBUS_COLORS['green']}
    labels_fr = {'High': 'Élevé', 'Medium': 'Modéré', 'Low': 'Faible'}
    filtered_plot = filtered.copy()
    filtered_plot['Niveau'] = filtered_plot['risk_level'].map(labels_fr)
    color_map_fr = {'Élevé': AIRBUS_COLORS['red'], 'Modéré': AIRBUS_COLORS['orange'], 'Faible': AIRBUS_COLORS['green']}

    fig_scatter = px.scatter(
        filtered_plot, x='mean_risk', y='max_risk', color='Niveau',
        color_discrete_map=color_map_fr, hover_name='aircraft_id',
        size='months', size_max=18,
        labels={'mean_risk': 'Risque moyen', 'max_risk': 'Risque max', 'months': 'Mois'},
    )
    fig_scatter.add_hline(y=0.7, line_dash='dot', line_color=AIRBUS_COLORS['red'], opacity=0.5)
    fig_scatter.add_vline(x=0.4, line_dash='dot', line_color=AIRBUS_COLORS['orange'], opacity=0.5)
    fig_scatter.update_layout(**PLOTLY_LAYOUT, height=380)
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("**Inventaire des appareils**")
    display = filtered.copy()
    display['Risque max'] = display['max_risk'].apply(lambda v: f"{v:.3f}")
    display['Risque moyen'] = display['mean_risk'].apply(lambda v: f"{v:.3f}")
    display['Niveau'] = display['risk_level'].map({'High': 'Élevé', 'Medium': 'Modéré', 'Low': 'Faible'})
    display['Mois suivis'] = display['months']
    display['Dernier relevé'] = display['last_month']
    display = display.rename(columns={'aircraft_id': 'Appareil'})

    def highlight_risk(val):
        if val == 'Élevé':  return 'color: #cc2222; font-weight: 700'
        if val == 'Modéré': return 'color: #b37400; font-weight: 700'
        return 'color: #007a3d; font-weight: 700'

    styled = display[['Appareil', 'Risque max', 'Risque moyen', 'Niveau', 'Mois suivis', 'Dernier relevé']
                     ].style.map(highlight_risk, subset=['Niveau'])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=420)

    st.markdown("---")
    st.markdown("**Saisonnalité du risque**")
    preds = get_predictions()
    preds['month_num'] = preds['year_month'].str[-2:].astype(int)
    preds['year'] = preds['year_month'].str[:4].astype(int)
    monthly = preds.groupby(['year', 'month_num'])['corrosion_risk'].mean().reset_index()
    pivot = monthly.pivot(index='year', columns='month_num', values='corrosion_risk')
    month_names = ['Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Jun', 'Jul', 'Aoû', 'Sep', 'Oct', 'Nov', 'Déc']
    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[month_names[i-1] for i in pivot.columns],
        y=pivot.index.astype(str),
        colorscale=[[0, AIRBUS_COLORS['navy']], [0.5, AIRBUS_COLORS['blue']], [1, AIRBUS_COLORS['red']]],
        showscale=True,
    ))
    fig_heat.update_layout(**PLOTLY_LAYOUT, height=350, xaxis_title="Mois", yaxis_title="Année")
    st.plotly_chart(fig_heat, use_container_width=True)
