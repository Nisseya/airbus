import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

import base64
import streamlit as st
from streamlit_option_menu import option_menu
from theme import AIRBUS_CSS


def _img_b64(path):
    with open(Path(__file__).parent / path, "rb") as f:
        return base64.b64encode(f.read()).decode()


st.set_page_config(
    page_title="Airbus | Surveillance Corrosion",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(AIRBUS_CSS, unsafe_allow_html=True)

with st.sidebar:
    logo = _img_b64("assets/airbus-logo.png")
    st.markdown(
        f"""
    <div style="padding:20px 12px 24px 12px; border-bottom:1px solid rgba(255,255,255,0.15); margin-bottom:8px;">
        <img src="data:image/png;base64,{logo}" style="height:60px;">
        <div style="font-size:10px; color:rgba(255,255,255,0.45); font-weight:600; letter-spacing:0.1em; margin-top:8px;">
            SURVEILLANCE CORROSION
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    selected = option_menu(
        menu_title=None,
        options=["Vue d'ensemble", "Flotte", "Détail appareil", "Simulateur", "Analyse & ROI"],
        icons=[
            "house-fill",
            "airplane-fill",
            "airplane-engines-fill",
            "eyedropper",
            "bar-chart-fill",
        ],
        default_index=0,
        styles={
            "container": {
                "padding": "0",
                "background-color": "transparent",
                "border-radius": "0",
                "border": "none",
                "box-shadow": "none",
            },
            "nav-link": {
                "font-size": "13px",
                "font-weight": "500",
                "color": "rgba(255,255,255,0.7)",
                "background-color": "transparent",
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
            "icon": {
                "color": "rgba(255,255,255,0.7)",
                "font-size": "15px",
            },
            "menu-title": {
                "color": "white",
            },
        },
    )

from views import overview, fleet, aircraft, simulator, insights

VIEWS = {
    "Vue d'ensemble": overview.show,
    "Flotte":         fleet.show,
    "Détail appareil":aircraft.show,
    "Simulateur":     simulator.show,
    "Analyse & ROI":  insights.show,
}

VIEWS[selected]()
