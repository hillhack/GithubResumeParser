"""
styles.py — All CSS for the GitHub Resume Parser Streamlit app.

Import and call inject_css() at the top of your Streamlit page.
"""

import streamlit as st

# ── Design tokens ────────────────────────────────────────────────────────────
COLORS = {
    "bg_primary":    "#0D1117",
    "bg_secondary":  "#161B22",
    "bg_card":       "#21262D",
    "accent":        "#7C3AED",
    "accent_2":      "#06B6D4",
    "accent_soft":   "#4F46E5",
    "text_primary":  "#E6EDF3",
    "text_muted":    "#8B949E",
    "border":        "#30363D",
    "success":       "#3FB950",
    "danger":        "#F85149",
    "warning":       "#D29922",
}

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Base ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: #0D1117; color: #E6EDF3; }
[data-testid="stSidebar"] {
    background: #161B22;
    border-right: 1px solid #30363D;
}

/* ── Hero header ── */
.hero {
    text-align: center;
    padding: 2rem 0 1.2rem;
    background: linear-gradient(135deg, #7C3AED22 0%, #06B6D422 100%);
    border-radius: 16px;
    margin-bottom: 1.5rem;
    border: 1px solid #30363D;
}
.hero h1 {
    font-size: 2.4rem;
    font-weight: 700;
    background: linear-gradient(135deg, #7C3AED, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin: 0;
}
.hero p { color: #8B949E; margin: 0.4rem 0 0; font-size: 1.05rem; }

/* ── Project cards ── */
.proj-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s, box-shadow 0.2s;
}
.proj-card:hover {
    border-color: #7C3AED;
    box-shadow: 0 0 0 1px #7C3AED44;
}
.proj-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 4px;
}
.proj-name { font-weight: 600; font-size: 1rem; color: #E6EDF3; }
.proj-score {
    font-size: 0.78rem;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 20px;
    background: #7C3AED33;
    color: #A78BFA;
}
.proj-desc { color: #8B949E; font-size: 0.85rem; margin: 4px 0 8px; }

/* ── Tags ── */
.tag {
    display: inline-block;
    background: #21262D;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 1px 8px;
    font-size: 0.75rem;
    color: #8B949E;
    margin: 2px 2px 0 0;
}

/* ── Skill badges ── */
.badge-matched {
    display: inline-block;
    background: #1A3A2A;
    border: 1px solid #3FB950;
    border-radius: 8px;
    padding: 3px 10px;
    font-size: 0.8rem;
    color: #3FB950;
    margin: 3px;
}
.badge-missing {
    display: inline-block;
    background: #3A1A1A;
    border: 1px solid #F85149;
    border-radius: 8px;
    padding: 3px 10px;
    font-size: 0.8rem;
    color: #F85149;
    margin: 3px;
}

/* ── Resume white-paper preview ── */
.resume-preview {
    background: #FFFFFF;
    color: #1A1A1A;
    border-radius: 10px;
    padding: 2.5rem 3rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.88rem;
    line-height: 1.65;
    max-width: 800px;
    margin: 0 auto;
    box-shadow: 0 8px 40px #00000066;
}
.resume-name { font-size: 1.9rem; font-weight: 700; color: #111; }
.resume-contact { color: #555; font-size: 0.82rem; margin: 4px 0 14px; }
.resume-section-title {
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.09em;
    color: #4F46E5;
    border-bottom: 2px solid #4F46E5;
    padding-bottom: 3px;
    margin: 18px 0 8px;
}
.resume-proj-name { font-weight: 600; color: #111; }
.resume-proj-tech { color: #555; font-size: 0.82rem; }
.resume-bullet { margin: 3px 0 3px 12px; color: #333; }
.resume-summary { color: #444; margin-bottom: 4px; }

/* ── Generate button ── */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #7C3AED, #4F46E5);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 1rem;
    padding: 0.65rem 2rem;
    width: 100%;
    transition: opacity 0.2s, transform 0.12s, box-shadow 0.2s;
}
div[data-testid="stButton"] > button:hover {
    opacity: 0.92;
    transform: translateY(-1px);
    box-shadow: 0 4px 16px #7C3AED55;
}
div[data-testid="stButton"] > button:active { transform: translateY(0); }

/* ── Inputs ── */
.stTextArea textarea, .stTextInput input {
    background: #21262D !important;
    border: 1px solid #30363D !important;
    color: #E6EDF3 !important;
    border-radius: 8px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: #7C3AED !important;
    box-shadow: 0 0 0 3px #7C3AED22 !important;
}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: #161B22;
    border-radius: 10px;
    padding: 4px;
    gap: 4px;
    border: 1px solid #30363D;
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    color: #8B949E;
    border-radius: 8px;
    font-weight: 500;
    padding: 6px 16px;
}
.stTabs [aria-selected="true"] {
    background: #7C3AED !important;
    color: white !important;
}

/* ── Sidebar labels ── */
.sidebar-label {
    font-size: 0.75rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: #8B949E;
    margin: 10px 0 4px;
}

/* ── Code blocks ── */
.stCodeBlock { border-radius: 10px; }

/* ── Divider ── */
hr { border-color: #30363D; }
"""


def inject_css() -> None:
    """Inject all app CSS into the Streamlit page."""
    st.markdown(f"<style>{CSS}</style>", unsafe_allow_html=True)
