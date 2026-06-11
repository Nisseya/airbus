import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from streamlit_option_menu import option_menu
from theme import AIRBUS_CSS

st.set_page_config(
    page_title="Airbus | Corrosion Risk Monitor",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(AIRBUS_CSS, unsafe_allow_html=True)

with st.sidebar:
    st.markdown("""
    <div style="padding:20px 12px 24px 12px; border-bottom:1px solid rgba(255,255,255,0.15); margin-bottom:8px;">
        <div style="font-size:24px; font-weight:800; letter-spacing:0.12em; color:white;">✈ AIRBUS</div>
        <div style="font-size:10px; color:rgba(255,255,255,0.45); font-weight:600; letter-spacing:0.1em; margin-top:4px;">
            CORROSION RISK MONITOR
        </div>
    </div>
    """, unsafe_allow_html=True)

    selected = option_menu(
        menu_title=None,
        options=["Overview", "Fleet", "Aircraft Detail", "Simulator", "Insights & ROI"],
        icons=["house-fill", "airplane-fill", "airplane-engines-fill", "eyedropper", "bar-chart-fill"],
        default_index=0,
        styles={
            "container":         {
                "padding": "4px 8px",
                "background-color": "#00205B",
            },
            "nav-link":          {
                "font-size": "13px",
                "font-weight": "500",
                "color": "rgba(255,255,255,0.7)",
                "background-color": "#00205B",
                "border-radius": "8px",
                "margin": "2px 0",
                "padding": "10px 14px",
                "--hover-color": "#003080",
            },
            "nav-link-selected": {
                "background-color": "rgba(0,130,200,0.4)",
                "color": "white",
                "font-weight": "600",
            },
            "icon":              {
                "color": "rgba(255,255,255,0.7)",
                "font-size": "15px",
            },
            "menu-title":        {
                "color": "white",
            },
        },
    )

from views import overview, fleet, aircraft, simulator, insights

VIEWS = {
    "Overview":      overview.show,
    "Fleet":         fleet.show,
    "Aircraft Detail": aircraft.show,
    "Simulator":     simulator.show,
    "Insights & ROI": insights.show,
}

VIEWS[selected]()
