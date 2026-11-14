import streamlit as st
import textwrap

# ==========================================================
# ENERGY INSIGHT — DESIGN SYSTEM
# ==========================================================

def apply_custom_css():

    st.markdown("""
    <style>

    /* ---------- COLOUR PALETTE ---------- */

    :root {
        --bg-primary: #0B1120;
        --bg-secondary: #111C2E;
        --bg-card: #172438;
        --bg-hover: #1D2D45;
        --accent: #38BDF8;
        --green: #34D399;
        --text-primary: #F1F5F9;
        --text-secondary: #94A3B8;
        --border: #26364D;
    }


    /* ---------- MAIN APPLICATION ---------- */

    .stApp {
        background: var(--bg-primary);
        color: var(--text-primary);
    }

    [data-testid="stHeader"] {
        background: transparent;
    }

    [data-testid="stMainBlockContainer"] {
        max-width: 1450px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }


    /* ---------- SIDEBAR ---------- */

    [data-testid="stSidebar"] {
        background: var(--bg-secondary);
        border-right: 1px solid var(--border);
    }

    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--text-primary);
    }


    /* ---------- TYPOGRAPHY ---------- */

    h1, h2, h3, h4 {
        color: var(--text-primary);
        letter-spacing: -0.5px;
    }

    p {
        color: var(--text-secondary);
    }


    /* ---------- WEBSITE HEADER ---------- */

    .website-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 12px 4px 22px 4px;
        border-bottom: 1px solid var(--border);
        margin-bottom: 30px;
    }

    .brand {
        font-size: 1.55rem;
        font-weight: 800;
        color: var(--text-primary);
        letter-spacing: -0.8px;
    }

    .brand span {
        color: var(--accent);
    }

    .brand-tagline {
        font-size: 0.75rem;
        color: var(--text-secondary);
        margin-top: 3px;
    }


    /* ---------- HERO SECTION ---------- */

    .hero-section {
        background:
            linear-gradient(
                120deg,
                #172D48 0%,
                #111C2E 60%,
                #0B1120 100%
            );

        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 42px;
        margin: 20px 0 30px 0;
    }

    .hero-label {
        color: var(--accent);
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 2px;
        text-transform: uppercase;
    }

    .hero-title {
        font-size: 2.6rem;
        font-weight: 800;
        line-height: 1.2;
        color: var(--text-primary);
        margin: 14px 0;
    }

    .hero-description {
        color: var(--text-secondary);
        font-size: 1.05rem;
        max-width: 700px;
        line-height: 1.8;
    }


    /* ---------- SECTION HEADINGS ---------- */

    .section-title {
        font-size: 1.35rem;
        font-weight: 700;
        color: var(--text-primary);
        margin-top: 30px;
        margin-bottom: 5px;
    }

    .section-description {
        font-size: 0.9rem;
        color: var(--text-secondary);
        margin-bottom: 18px;
    }


    /* ---------- KPI CARDS ---------- */

    [data-testid="stMetric"] {
        background: var(--bg-card);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 20px;
        transition: 0.2s ease;
    }

    [data-testid="stMetric"]:hover {
        background: var(--bg-hover);
        border-color: var(--accent);
        transform: translateY(-2px);
    }

    [data-testid="stMetricLabel"] {
        color: var(--text-secondary);
    }

    [data-testid="stMetricValue"] {
        color: var(--text-primary);
        font-weight: 700;
    }


    /* ---------- CHARTS ---------- */

    div[data-testid="stPlotlyChart"] {
        background: var(--bg-secondary);
        border: 1px solid var(--border);
        border-radius: 14px;
        padding: 10px;
    }


    /* ---------- DATA TABLES ---------- */

    div[data-testid="stDataFrame"] {
        border: 1px solid var(--border);
        border-radius: 12px;
        overflow: hidden;
    }


    /* ---------- BUTTONS ---------- */

    .stButton > button {
        background: var(--accent);
        color: #07111F;
        border: none;
        border-radius: 8px;
        font-weight: 700;
        padding: 8px 18px;
    }

    .stButton > button:hover {
        background: #7DD3FC;
        color: #07111F;
    }


    /* ---------- FOOTER ---------- */

    .website-footer {
        border-top: 1px solid var(--border);
        margin-top: 55px;
        padding: 35px 5px 15px 5px;
    }

    .footer-brand {
        font-size: 1.3rem;
        font-weight: 800;
        color: var(--text-primary);
    }

    .footer-heading {
        font-weight: 700;
        color: var(--text-primary);
        margin-bottom: 12px;
    }

    .footer-text {
        color: var(--text-secondary);
        font-size: 0.85rem;
        line-height: 1.9;
    }

    .footer-bottom {
        border-top: 1px solid var(--border);
        margin-top: 25px;
        padding-top: 18px;
        color: var(--text-secondary);
        font-size: 0.78rem;
        text-align: center;
    }
    .footer-link {
    color: var(--text-secondary);
    text-decoration: none;
    transition: 0.2s ease;
}

.footer-link:hover {
    color: var(--accent);
    padding-left: 4px;
}

    hr {
        border-color: var(--border);
    }

    </style>
    """, unsafe_allow_html=True)


# ==========================================================
# WEBSITE HEADER
# ==========================================================

def render_site_header():

    col1, col2 = st.columns([1.2, 3.8])

    with col1:

        st.markdown(
            textwrap.dedent("""
            <div>
                <div class="brand">
                    ⚡ ENERGY<span>INSIGHT</span>
                </div>
                <div class="brand-tagline">
                    Smart Energy Analytics
                </div>
            </div>
            """),
            unsafe_allow_html=True
        )

    with col2:

        selected_page = st.radio(
            "Navigation",
            [
                "Overview",
                "Consumption Analysis",
                "Cost Analysis",
                "Forecast & Anomalies",
                "Data Explorer"
            ],
            horizontal=True,
            label_visibility="collapsed",
            key="top_navigation"
        )

    st.markdown("---")

    return selected_page


def render_header():

    st.markdown(
        '<div class="main-title">⚡ ENERGY INSIGHT</div>',
        unsafe_allow_html=True
    )

    st.markdown(
        '<div class="main-subtitle">'
        'Smart Household Energy Analytics & Forecasting Platform'
        '</div>',
        unsafe_allow_html=True
    )
# ==========================================================
# HERO SECTION
# ==========================================================

def render_hero():

    hero_html = """
    <div class="hero-section">
    <div class="hero-label">SMART ENERGY ANALYTICS PLATFORM</div>
    <div class="hero-title">Understand Your Energy.<br>Make Smarter Decisions.</div>
    <div class="hero-description">Explore household electricity consumption, discover usage patterns, estimate energy costs and investigate future consumption through data-driven analytics.</div>
    </div>
    """

    st.markdown(hero_html, unsafe_allow_html=True)


# ==========================================================
# EXISTING HEADER FUNCTION
# ==========================================================

def render_header():

    render_site_header()


# ==========================================================
# SECTION TITLE
# ==========================================================

def render_section_title(title, description=None):

    st.markdown(
        f'<div class="section-title">{title}</div>',
        unsafe_allow_html=True
    )

    if description:

        st.markdown(
            f'<div class="section-description">'
            f'{description}</div>',
            unsafe_allow_html=True
        )


# ==========================================================
# KPI CARDS
# ==========================================================

def render_kpi_cards(
    total_energy,
    average_daily,
    peak_consumption,
    estimated_cost,
    data_coverage,
    deltas=None
):

    deltas = deltas or {}

    columns = st.columns(5)

    metrics = [
        ("Total Energy", f"{total_energy:,.1f} kWh"),
        ("Daily Average", f"{average_daily:,.2f} kWh"),
        ("Peak Hour", f"{peak_consumption:,.2f} kWh"),
        ("Estimated Cost", f"€{estimated_cost:,.2f}"),
        ("Data Coverage", f"{data_coverage:.1f}%")
    ]

    for column, (label, value) in zip(columns, metrics):

        with column:

            st.metric(
                label=label,
                value=value,
                delta=deltas.get(label),
                delta_color="normal"
            )


# ==========================================================
# WEBSITE FOOTER
# ==========================================================
def render_footer():

    st.markdown("---")

    col1, col2, col3 = st.columns(3)

    with col1:

        st.markdown(
            textwrap.dedent("""
            <div class="footer-heading">ABOUT</div>
            <div class="footer-text">
                Energy Insight<br>
                Household Energy Analytics<br>
                Consumption & Forecasting
            </div>
            """),
            unsafe_allow_html=True
        )

    with col2:

        st.markdown(
            textwrap.dedent("""
            <div class="footer-heading">TECHNOLOGIES</div>
            <div class="footer-text">
                Python<br>
                Pandas & NumPy<br>
                SQLite · Plotly · Streamlit
            </div>
            """),
            unsafe_allow_html=True
        )

    with col3:

        st.markdown(
            textwrap.dedent("""
            <div class="footer-heading">CONNECT</div>
<div class="footer-text">
    <a class="footer-link" href="https://github.com/ashi282007" target="_blank">GitHub</a><br>
    <a class="footer-link" href="https://www.linkedin.com/in/YOUR-NAME" target="_blank">LinkedIn</a><br>
    <a class="footer-link" href="https://github.com/ashi282007/YOUR-REPO" target="_blank">Documentation</a>
</div>
            """),
            unsafe_allow_html=True
        )

    st.markdown(
        textwrap.dedent("""
        <div class="footer-bottom">
            © 2026 Energy Insight · All rights reserved.
        </div>
        """),
        unsafe_allow_html=True
    )