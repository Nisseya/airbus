import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from model import get_fleet_summary, get_predictions
from theme import PLOTLY_LAYOUT, AIRBUS_COLORS


def show():
    fleet = get_fleet_summary()

    st.markdown("""
    <div class="page-header">
        <h1>Fleet Management</h1>
        <p>Full aircraft inventory with corrosion risk assessment</p>
    </div>
    """, unsafe_allow_html=True)

    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        risk_filter = st.multiselect("Risk Level", ['High', 'Medium', 'Low'], default=['High', 'Medium', 'Low'])
    with col_f2:
        sort_by = st.selectbox("Sort by", ['max_risk', 'mean_risk', 'months'], format_func=lambda x: {
            'max_risk': 'Peak Risk', 'mean_risk': 'Avg Risk', 'months': 'Months Tracked'}[x])
    with col_f3:
        min_risk = st.slider("Min. Peak Risk", 0.0, 1.0, 0.0, 0.05)

    filtered = fleet[
        fleet['risk_level'].isin(risk_filter) & (fleet['max_risk'] >= min_risk)
    ].sort_values(sort_by, ascending=False)

    st.caption(f"Showing {len(filtered)} of {len(fleet)} aircraft")

    st.markdown("**Risk Profile — Peak vs. Average**")
    color_map = {'High': AIRBUS_COLORS['red'], 'Medium': AIRBUS_COLORS['orange'], 'Low': AIRBUS_COLORS['green']}
    fig_scatter = px.scatter(
        filtered, x='mean_risk', y='max_risk', color='risk_level',
        color_discrete_map=color_map, hover_name='aircraft_id',
        size='months', size_max=18,
        labels={'mean_risk': 'Average Risk', 'max_risk': 'Peak Risk', 'months': 'Months'},
    )
    fig_scatter.add_hline(y=0.7, line_dash='dot', line_color=AIRBUS_COLORS['red'], opacity=0.5)
    fig_scatter.add_vline(x=0.4, line_dash='dot', line_color=AIRBUS_COLORS['orange'], opacity=0.5)
    fig_scatter.update_layout(**PLOTLY_LAYOUT, height=380)
    st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("**Aircraft Inventory**")
    display = filtered.copy()
    display['Peak Risk'] = display['max_risk'].apply(lambda v: f"{v:.3f}")
    display['Avg Risk'] = display['mean_risk'].apply(lambda v: f"{v:.3f}")
    display['Risk Level'] = display['risk_level']
    display['Months'] = display['months']
    display['Last Record'] = display['last_month']
    display = display.rename(columns={'aircraft_id': 'Aircraft ID'})

    def highlight_risk(val):
        if val == 'High':   return 'color: #cc2222; font-weight: 700'
        if val == 'Medium': return 'color: #b37400; font-weight: 700'
        return 'color: #007a3d; font-weight: 700'

    styled = display[['Aircraft ID', 'Peak Risk', 'Avg Risk', 'Risk Level', 'Months', 'Last Record']
                     ].style.map(highlight_risk, subset=['Risk Level'])
    st.dataframe(styled, use_container_width=True, hide_index=True, height=420)

    st.markdown("---")
    st.markdown("**Seasonal Risk Patterns**")
    preds = get_predictions()
    preds['month_num'] = preds['year_month'].str[-2:].astype(int)
    preds['year'] = preds['year_month'].str[:4].astype(int)
    monthly = preds.groupby(['year', 'month_num'])['corrosion_risk'].mean().reset_index()
    pivot = monthly.pivot(index='year', columns='month_num', values='corrosion_risk')
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    fig_heat = go.Figure(go.Heatmap(
        z=pivot.values,
        x=[month_names[i-1] for i in pivot.columns],
        y=pivot.index.astype(str),
        colorscale=[[0, AIRBUS_COLORS['navy']], [0.5, AIRBUS_COLORS['blue']], [1, AIRBUS_COLORS['red']]],
        showscale=True,
    ))
    fig_heat.update_layout(**PLOTLY_LAYOUT, height=350, xaxis_title="Month", yaxis_title="Year")
    st.plotly_chart(fig_heat, use_container_width=True)
