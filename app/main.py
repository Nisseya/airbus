import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from theme import AIRBUS_CSS

st.set_page_config(
    page_title="Airbus | Corrosion Risk Monitor",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(AIRBUS_CSS, unsafe_allow_html=True)

pages = st.navigation(
    {
        "": [
            st.Page("pages/0_Overview.py",  title="Overview",        icon="🏠", default=True),
        ],
        "Analysis": [
            st.Page("pages/1_Fleet.py",     title="Fleet",           icon="🛫"),
            st.Page("pages/2_Aircraft.py",  title="Aircraft Detail", icon="✈️"),
        ],
        "Tools": [
            st.Page("pages/3_Simulator.py", title="Simulator",       icon="🔬"),
            st.Page("pages/4_Insights.py",  title="Insights & ROI",  icon="📊"),
        ],
    }
)

with st.sidebar:
    st.markdown("""
    <div style="padding: 20px 12px 24px 12px; border-bottom: 1px solid rgba(255,255,255,0.15); margin-bottom: 8px;">
        <div style="font-size: 24px; font-weight: 800; letter-spacing: 0.12em; color: white;">✈ AIRBUS</div>
        <div style="font-size: 10px; color: rgba(255,255,255,0.5); font-weight: 600; letter-spacing: 0.1em; margin-top: 4px;">
            CORROSION RISK MONITOR
        </div>
    </div>
    """, unsafe_allow_html=True)

pages.run()
