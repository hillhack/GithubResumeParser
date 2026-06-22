"""
client.py — Main Streamlit entry point for GitHub Resume Parser.

Thin orchestrator: imports styles, components, and backend agents.
Run with: streamlit run client.py
"""

import streamlit as st
from dotenv import load_dotenv

import github_extractor as gh
import jd_analyzer as jda
import repo_ranker as rr
import resume_generator as rg
import latex_generator as lg
from styles import inject_css
from utils import get_groq_client, init_session
from components import (
    render_hero,
    render_sidebar,
    render_empty_state,
    render_resume_tab,
    render_projects_tab,
    render_skills_tab,
    render_latex_tab,
)

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Resume Parser",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()


# ── Utilities imported from utils.py ─────────────────────────────────────────
# get_groq_client, init_session


# ── Generation pipeline ───────────────────────────────────────────────────────

def run_pipeline(username: str, jd_text: str, pages: int, template: str, ranking: str) -> None:
    """
    Execute the full JD → GitHub → Resume pipeline with live progress.

    Stages:
        1. GitHub extraction
        2. JD analysis
        3. Repo scoring & ranking
        4. Resume content generation
        5. LaTeX generation
    """
    client = get_groq_client()
    prefs = {"pages": pages, "template": template}

    try:
        with st.status("🔍 Extracting GitHub profile…", expanded=True) as status:

            # Stage 1 — GitHub
            st.write(f"Fetching @{username}'s profile, repos, READMEs…")
            github_data = gh.extract_full_profile(username)
            st.session_state["github_data"] = github_data
            n_repos = len(github_data["repos"])
            st.write(f"✅ Found **{n_repos}** repositories")

            # Stage 2 — JD
            status.update(label="🧠 Analyzing job description…")
            st.write("Extracting skills, domain, experience level…")
            jd_analysis = jda.analyze_jd(jd_text, client)
            st.session_state["jd_analysis"] = jd_analysis
            st.write(
                f"✅ Role: **{jd_analysis['role_title']}** | "
                f"Domain: **{jd_analysis['domain']}**"
            )

            # Stage 3 — Scoring & ranking
            status.update(label="🏆 Scoring & ranking repositories…")
            cap = min(n_repos, 20)
            st.write(f"Scoring top {cap} repos against JD…")
            repos = github_data["repos"]
            scored = rr.score_repos_with_jd(repos[:cap], jd_analysis, client)
            github_data["repos"][:cap] = scored

            ranked = (
                rr.rank_by_jd(scored) + repos[cap:]
                if ranking == "JD Relevance"
                else rr.rank_by_popularity(repos)
            )
            st.session_state["ranked_repos"] = ranked
            st.session_state["repo_order"] = list(range(len(ranked)))
            top = ranked[0]
            st.write(
                f"✅ Top match: **{top['name']}** "
                f"({top.get('relevance_score', 0):.0%})"
            )

            # Stage 4 — Resume content
            status.update(label="✍️ Generating resume content…")
            st.write("Writing bullets, summary, skills section…")
            resume_data = rg.generate_full_resume(
                github_data, ranked, jd_analysis, prefs, client
            )
            st.session_state["resume_data"] = resume_data
            st.write(f"✅ Generated **{len(resume_data['projects'])}** project sections")

            # Stage 5 — LaTeX
            status.update(label="📄 Building LaTeX source…")
            latex_code = lg.generate_latex(resume_data, template)
            st.session_state["latex_code"] = latex_code
            st.session_state["generated"] = True
            st.session_state["error"] = None

            status.update(label="✅ Done! Review your resume below.", state="complete")

    except Exception as exc:
        st.session_state["error"] = str(exc)
        st.error(f"Pipeline error: {exc}")
        st.stop()


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    init_session()
    render_hero()

    username, pages, template, ranking = render_sidebar()

    # ── Input row ─────────────────────────────────────────────────────────────
    col_jd, col_btn = st.columns([3, 1])
    with col_jd:
        jd_text = st.text_area(
            "📋 **Job Description**",
            placeholder=(
                "Paste the full job description here…\n\n"
                "Example:\nWe are looking for an ML Engineer with experience in "
                "Python, LLMs, RAG pipelines, and vector databases…"
            ),
            height=200,
            key="jd_text",
        )
    with col_btn:
        st.markdown("<br>", unsafe_allow_html=True)
        generate = st.button("🚀 Generate Resume", use_container_width=True)
        if st.session_state.get("error"):
            st.error(st.session_state["error"])

    # ── Trigger pipeline ──────────────────────────────────────────────────────
    if generate:
        if not username:
            st.warning("⚠️ Enter a GitHub username in the sidebar.")
            st.stop()
        if not jd_text.strip():
            st.warning("⚠️ Paste a job description first.")
            st.stop()
        run_pipeline(username, jd_text, pages, template, ranking)

    # ── Results ───────────────────────────────────────────────────────────────
    if not st.session_state.get("generated"):
        render_empty_state()
        return

    resume_data  = st.session_state["resume_data"]
    ranked_repos = st.session_state["ranked_repos"]
    jd_analysis  = st.session_state["jd_analysis"]
    latex_code   = st.session_state["latex_code"]

    tab_resume, tab_projects, tab_skills, tab_latex = st.tabs(
        ["📄 Resume", "🏆 Projects", "🎯 Skills Gap", "⚙️ LaTeX"]
    )

    with tab_resume:
        render_resume_tab(resume_data, latex_code)

    with tab_projects:
        render_projects_tab(ranked_repos, pages, template, jd_analysis)

    with tab_skills:
        render_skills_tab(resume_data, jd_analysis)

    with tab_latex:
        render_latex_tab(latex_code)


if __name__ == "__main__":
    main()
