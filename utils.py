"""utils.py — Shared utilities for GitHub Resume Parser."""

import os
import streamlit as st
from groq import Groq


def get_groq_client() -> Groq:
    """Return an authenticated Groq client, halting the app if key is missing."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("⚠️ GROQ_API_KEY not set. Add it to your .env file.")
        st.stop()
    return Groq(api_key=api_key)


def init_session() -> None:
    """Initialise all session-state keys with safe defaults."""
    defaults: dict = {
        "generated": False,
        "github_data": None,
        "jd_analysis": None,
        "ranked_repos": None,
        "resume_data": None,
        "latex_code": None,
        "repo_order": None,
        "error": None,
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val
