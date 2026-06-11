AIRBUS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif !important; }

#MainMenu, footer { visibility: hidden; }
header { visibility: hidden; }

/* ─── Background ─────────────────────────────────── */
.stApp {
    background: #F0F4F8;
}

/* ─── Sidebar ─────────────────────────────────────── */
[data-testid="stSidebar"] {
    background: #00205B !important;
}
[data-testid="stSidebar"] * {
    color: white !important;
}
[data-testid="stSidebarNavLink"] {
    border-radius: 8px !important;
    margin: 2px 8px !important;
    color: rgba(255,255,255,0.75) !important;
    transition: all 0.2s !important;
}
[data-testid="stSidebarNavLink"]:hover {
    background: rgba(255,255,255,0.12) !important;
    color: white !important;
}
[data-testid="stSidebarNavLink"][aria-current="page"] {
    background: rgba(0,130,200,0.35) !important;
    color: white !important;
    border-left: 3px solid #0082C8 !important;
}

/* ─── Main text ───────────────────────────────────── */
h1, h2, h3, h4, h5, h6 {
    color: #00205B !important;
}
.stMarkdown p, p, span, label {
    color: #1a2e4a !important;
}

/* ─── Metrics ─────────────────────────────────────── */
[data-testid="stMetric"] {
    background: white !important;
    border: 1px solid #d6e4f0 !important;
    border-top: 3px solid #0082C8 !important;
    border-radius: 12px !important;
    padding: 20px !important;
    box-shadow: 0 2px 8px rgba(0,32,91,0.06) !important;
    transition: box-shadow 0.2s, transform 0.2s !important;
}
[data-testid="stMetric"]:hover {
    box-shadow: 0 6px 20px rgba(0,32,91,0.12) !important;
    transform: translateY(-2px) !important;
}
[data-testid="stMetricValue"] {
    color: #00205B !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}
[data-testid="stMetricLabel"] {
    color: #6b7e9a !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.06em !important;
}
[data-testid="stMetricDelta"] { font-size: 0.85rem !important; }

/* ─── Buttons ─────────────────────────────────────── */
.stButton > button {
    background: #0082C8 !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    padding: 10px 28px !important;
    transition: all 0.2s ease !important;
    letter-spacing: 0.02em !important;
    box-shadow: 0 2px 8px rgba(0,130,200,0.3) !important;
}
.stButton > button:hover {
    background: #005fa3 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 16px rgba(0,130,200,0.4) !important;
}

/* ─── Selectbox / Input ───────────────────────────── */
.stSelectbox > div > div,
.stMultiSelect > div > div {
    background: white !important;
    border: 1px solid #c8d9ea !important;
    border-radius: 8px !important;
    color: #00205B !important;
}

/* ─── Sliders ─────────────────────────────────────── */
[data-testid="stSlider"] > div > div > div > div {
    background: #0082C8 !important;
}

/* ─── Tabs ────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
    background: white !important;
    border-radius: 10px !important;
    padding: 4px !important;
    gap: 4px !important;
    border: 1px solid #d6e4f0 !important;
}
.stTabs [data-baseweb="tab"] {
    color: #6b7e9a !important;
    border-radius: 8px !important;
    padding: 8px 20px !important;
    font-weight: 500 !important;
}
.stTabs [aria-selected="true"] {
    background: #0082C8 !important;
    color: white !important;
}

/* ─── Dataframe ───────────────────────────────────── */
[data-testid="stDataFrame"] {
    border: 1px solid #d6e4f0 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
    background: white !important;
    box-shadow: 0 2px 8px rgba(0,32,91,0.06) !important;
}

/* ─── Divider ─────────────────────────────────────── */
hr { border-color: #d6e4f0 !important; }

/* ─── Custom components ───────────────────────────── */
.airbus-card {
    background: white;
    border: 1px solid #d6e4f0;
    border-radius: 14px;
    padding: 22px;
    box-shadow: 0 2px 8px rgba(0,32,91,0.06);
    margin-bottom: 14px;
    transition: box-shadow 0.2s, transform 0.2s;
}
.airbus-card:hover {
    box-shadow: 0 6px 20px rgba(0,32,91,0.1);
    transform: translateY(-2px);
}

.page-header {
    padding: 8px 0 20px 0;
    margin-bottom: 8px;
    border-bottom: 2px solid #0082C8;
}
.page-header h1 {
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    color: #00205B !important;
    letter-spacing: -0.02em !important;
    margin: 0 !important;
}
.page-header p {
    color: #6b7e9a !important;
    margin: 4px 0 0 0 !important;
    font-size: 0.9rem !important;
}

.risk-high {
    background: #fff0f0;
    border: 1px solid #ffb3b3;
    color: #cc2222 !important;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.risk-medium {
    background: #fff8e6;
    border: 1px solid #ffd580;
    color: #b37400 !important;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.risk-low {
    background: #f0fff7;
    border: 1px solid #80e6b3;
    color: #007a3d !important;
    border-radius: 20px;
    padding: 3px 10px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.kpi-label {
    color: #6b7e9a;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 4px;
}
.kpi-value {
    color: #00205B;
    font-size: 2.2rem;
    font-weight: 800;
    line-height: 1;
}
.kpi-value-blue { color: #0082C8 !important; }
.kpi-value-red  { color: #cc2222 !important; }
.kpi-value-green { color: #007a3d !important; }
.kpi-sub {
    color: #9aacbf;
    font-size: 12px;
    margin-top: 4px;
}
</style>
"""

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,32,91,0.02)',
    font=dict(color='#1a2e4a', family='Inter'),
    colorway=['#0082C8', '#00205B', '#FF6600', '#00aa55', '#cc2222', '#7c3aed'],
    xaxis=dict(gridcolor='#e8eef4', color='#6b7e9a', linecolor='#d6e4f0'),
    yaxis=dict(gridcolor='#e8eef4', color='#6b7e9a', linecolor='#d6e4f0'),
    legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(color='#1a2e4a')),
    margin=dict(l=16, r=16, t=40, b=16),
)

AIRBUS_COLORS = {
    'navy': '#00205B',
    'blue': '#0082C8',
    'light_blue': '#4db8f0',
    'orange': '#FF6600',
    'green': '#00aa55',
    'red': '#cc2222',
    'white': '#FFFFFF',
    'bg': '#F0F4F8',
    'card': '#FFFFFF',
    'border': '#d6e4f0',
    'text': '#1a2e4a',
    'muted': '#6b7e9a',
}
