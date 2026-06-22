"""Streamlit frontend — GitHub Resume Parser."""

import os
import time
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

import github_extractor as gh
import jd_analyzer as jda
import repo_ranker as rr
import resume_generator as rg
import latex_generator as lg

load_dotenv()

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GitHub Resume Parser",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Dark background */
.stApp { background: #0D1117; color: #E6EDF3; }
[data-testid="stSidebar"] { background: #161B22; border-right: 1px solid #30363D; }

/* Hero header */
.hero {
    text-align: center;
    padding: 2rem 0 1rem;
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

/* Stat cards */
.stat-row { display: flex; gap: 12px; margin: 1rem 0; }
.stat-card {
    flex: 1;
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
}
.stat-card .num { font-size: 1.6rem; font-weight: 700; color: #7C3AED; }
.stat-card .lbl { font-size: 0.78rem; color: #8B949E; margin-top: 2px; }

/* Project cards */
.proj-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 12px;
    padding: 1.1rem 1.3rem;
    margin-bottom: 0.8rem;
    transition: border-color 0.2s;
}
.proj-card:hover { border-color: #7C3AED; }
.proj-header { display: flex; align-items: center; justify-content: space-between; }
.proj-name { font-weight: 600; font-size: 1rem; color: #E6EDF3; }
.proj-score {
    font-size: 0.78rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    background: #7C3AED33;
    color: #A78BFA;
}
.proj-desc { color: #8B949E; font-size: 0.85rem; margin: 4px 0 8px; }
.tag {
    display: inline-block;
    background: #21262D;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 1px 7px;
    font-size: 0.75rem;
    color: #8B949E;
    margin: 2px 2px 0 0;
}

/* Skill badges */
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

/* Resume preview */
.resume-preview {
    background: #FFFFFF;
    color: #1A1A1A;
    border-radius: 10px;
    padding: 2.5rem 3rem;
    font-family: 'Inter', sans-serif;
    font-size: 0.88rem;
    line-height: 1.6;
    max-width: 800px;
    margin: 0 auto;
    box-shadow: 0 8px 32px #00000055;
}
.resume-name { font-size: 1.8rem; font-weight: 700; color: #111; }
.resume-contact { color: #555; font-size: 0.82rem; margin: 4px 0 12px; }
.resume-section-title {
    font-size: 0.9rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: #4F46E5;
    border-bottom: 2px solid #4F46E5;
    padding-bottom: 2px;
    margin: 16px 0 8px;
}
.resume-proj-name { font-weight: 600; color: #111; }
.resume-proj-tech { color: #555; font-size: 0.82rem; }
.resume-bullet { margin: 3px 0; color: #333; }
.resume-summary { color: #444; margin-bottom: 4px; }

/* Generate button */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #7C3AED, #4F46E5);
    color: white;
    border: none;
    border-radius: 10px;
    font-weight: 600;
    font-size: 1rem;
    padding: 0.6rem 2rem;
    width: 100%;
    transition: opacity 0.2s, transform 0.1s;
}
div[data-testid="stButton"] > button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}

/* Text areas & inputs */
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

/* Tabs */
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
}
.stTabs [aria-selected="true"] {
    background: #7C3AED !important;
    color: white !important;
}

/* Code block */
.stCodeBlock { border-radius: 10px; }

/* Sidebar labels */
.sidebar-label {
    font-size: 0.78rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #8B949E;
    margin-bottom: 4px;
}
</style>
""", unsafe_allow_html=True)


# ── Helpers ──────────────────────────────────────────────────────────────────

def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        st.error("⚠️ GROQ_API_KEY not set in .env file.")
        st.stop()
    return Groq(api_key=api_key)


def init_session():
    defaults = {
        "generated": False,
        "github_data": None,
        "jd_analysis": None,
        "ranked_repos": None,
        "resume_data": None,
        "latex_code": None,
        "repo_order": None,
        "error": None,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render_resume_preview(data: dict) -> str:
    profile = data["profile"]
    name = profile.get("name", profile.get("username", ""))
    email = profile.get("email", "")
    github_url = profile.get("html_url", "")
    location = profile.get("location", "")
    blog = profile.get("blog", "")

    contact_parts = []
    if location:
        contact_parts.append(location)
    if email:
        contact_parts.append(f'<a href="mailto:{email}" style="color:#4F46E5">{email}</a>')
    if github_url:
        contact_parts.append(f'<a href="{github_url}" style="color:#4F46E5">GitHub</a>')
    if blog:
        blog_url = blog if blog.startswith("http") else f"https://{blog}"
        contact_parts.append(f'<a href="{blog_url}" style="color:#4F46E5">Portfolio</a>')

    html = f"""<div class="resume-preview">
<div class="resume-name">{name}</div>
<div class="resume-contact">{" &nbsp;|&nbsp; ".join(contact_parts)}</div>"""

    summary = data.get("summary", "")
    if summary:
        html += f"""<div class="resume-section-title">Professional Summary</div>
<div class="resume-summary">{summary}</div>"""

    skills = data.get("skills_section", {})
    if skills:
        html += '<div class="resume-section-title">Technical Skills</div>'
        for cat, items in skills.items():
            if items:
                html += f'<div style="margin-bottom:4px"><strong>{cat}:</strong> {", ".join(items)}</div>'

    projects = data.get("projects", [])
    if projects:
        html += '<div class="resume-section-title">Projects</div>'
        for proj in projects:
            tech = " · ".join(proj.get("tech_stack", [])[:5])
            bullets_html = "".join(
                f'<div class="resume-bullet">• {b}</div>'
                for b in proj.get("bullets", [])
            )
            url = proj.get("url", "")
            name_html = f'<a href="{url}" style="color:#4F46E5;font-weight:600">{proj["name"]}</a>' if url else f'<span class="resume-proj-name">{proj["name"]}</span>'
            html += f"""<div style="margin-bottom:10px">
<div>{name_html} <span class="resume-proj-tech">| {tech}</span></div>
{bullets_html}
</div>"""

    html += "</div>"
    return html


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("## 🎯 Resume Settings")
        st.divider()

        st.markdown('<div class="sidebar-label">GitHub Username</div>', unsafe_allow_html=True)
        username = st.text_input("GitHub Username", placeholder="e.g. torvalds", key="username", label_visibility="collapsed")

        st.markdown('<div class="sidebar-label">Resume Length</div>', unsafe_allow_html=True)
        pages = st.radio("Resume Length", ["1 Page", "2 Pages"], key="pages", label_visibility="collapsed")

        st.markdown('<div class="sidebar-label">Template</div>', unsafe_allow_html=True)
        template = st.radio(
            "Template",
            ["ATS Classic", "Modern", "Research"],
            key="template",
            label_visibility="collapsed",
        )

        st.markdown('<div class="sidebar-label">Ranking Mode</div>', unsafe_allow_html=True)
        ranking = st.radio(
            "Ranking Mode",
            ["JD Relevance", "Popularity"],
            key="ranking",
            label_visibility="collapsed",
        )

        st.divider()
        if st.button("🔄 Reset", use_container_width=True):
            for k in ["generated", "github_data", "jd_analysis", "ranked_repos",
                      "resume_data", "latex_code", "repo_order", "error"]:
                st.session_state[k] = None if k != "generated" else False
            st.rerun()

        # Profile preview
        if st.session_state.get("github_data"):
            p = st.session_state["github_data"]["profile"]
            st.divider()
            if p.get("avatar_url"):
                st.image(p["avatar_url"], width=80)
            st.markdown(f"**{p.get('name', p.get('username'))}**")
            if p.get("bio"):
                st.caption(p["bio"])
            col1, col2 = st.columns(2)
            col1.metric("⭐ Stars", st.session_state["github_data"].get("total_stars", 0))
            col2.metric("📦 Repos", p.get("public_repos", 0))

    return username, int(pages[0]), template, ranking


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    init_session()

    # Header
    st.markdown("""
<div class="hero">
  <h1>🎯 GitHub Resume Parser</h1>
  <p>JD → GitHub → ATS Resume &nbsp;·&nbsp; Powered by Groq LLM</p>
</div>
""", unsafe_allow_html=True)

    username, pages, template, ranking = render_sidebar()

    # Input area
    col_jd, col_gen = st.columns([3, 1])
    with col_jd:
        jd_text = st.text_area(
            "📋 **Job Description**",
            placeholder="Paste the full job description here…\n\nExample:\nWe are looking for an ML Engineer with experience in Python, LLMs, RAG pipelines, and vector databases…",
            height=200,
            key="jd_text",
        )
    with col_gen:
        st.markdown("<br>", unsafe_allow_html=True)
        generate = st.button("🚀 Generate Resume", use_container_width=True)

        if st.session_state.get("error"):
            st.error(st.session_state["error"])

    # ── Generation pipeline ───────────────────────────────────────────────────
    if generate:
        if not username:
            st.warning("⚠️ Enter a GitHub username in the sidebar.")
            st.stop()
        if not jd_text.strip():
            st.warning("⚠️ Paste a job description first.")
            st.stop()

        client = get_groq_client()
        prefs = {"pages": pages, "template": template}

        try:
            with st.status("🔍 Extracting GitHub profile…", expanded=True) as status:
                st.write(f"Fetching @{username}'s profile, repos, READMEs…")
                github_data = gh.extract_full_profile(username)
                st.session_state["github_data"] = github_data
                n_repos = len(github_data["repos"])
                st.write(f"✅ Found {n_repos} repositories")

                status.update(label="🧠 Analyzing job description…")
                st.write("Extracting required skills, domain, experience level…")
                jd_analysis = jda.analyze_jd(jd_text, client)
                st.session_state["jd_analysis"] = jd_analysis
                st.write(f"✅ Role: **{jd_analysis['role_title']}** | Domain: **{jd_analysis['domain']}**")

                status.update(label="🏆 Scoring & ranking repositories…")
                st.write(f"Scoring {min(n_repos, 20)} repos against JD…")
                repos = github_data["repos"]
                scored = rr.score_repos_with_jd(repos[:20], jd_analysis, client)
                github_data["repos"][:20] = scored

                if ranking == "JD Relevance":
                    ranked = rr.rank_by_jd(scored) + repos[20:]
                else:
                    ranked = rr.rank_by_popularity(repos)

                st.session_state["ranked_repos"] = ranked
                st.session_state["repo_order"] = list(range(len(ranked)))
                st.write(f"✅ Top match: **{ranked[0]['name']}** ({ranked[0].get('relevance_score', 0):.0%})")

                status.update(label="✍️ Generating resume content…")
                st.write("Writing bullets, summary, skills section…")
                resume_data = rg.generate_full_resume(
                    github_data, ranked, jd_analysis, prefs, client
                )
                st.session_state["resume_data"] = resume_data
                st.write(f"✅ Generated {len(resume_data['projects'])} project sections")

                status.update(label="📄 Building LaTeX source…")
                latex_code = lg.generate_latex(resume_data, template)
                st.session_state["latex_code"] = latex_code
                st.session_state["generated"] = True
                st.session_state["error"] = None

                status.update(label="✅ Done! Scroll down to view your resume.", state="complete")

        except Exception as e:
            st.session_state["error"] = f"Error: {e}"
            st.error(f"Something went wrong: {e}")
            st.stop()

    # ── Results ───────────────────────────────────────────────────────────────
    if not st.session_state.get("generated"):
        st.markdown("""
<div style="text-align:center;padding:4rem 0;color:#8B949E">
  <div style="font-size:4rem">🚀</div>
  <div style="font-size:1.1rem;margin-top:0.5rem">Enter your GitHub username, paste a job description,<br>and click <strong>Generate Resume</strong></div>
</div>
""", unsafe_allow_html=True)
        return

    resume_data = st.session_state["resume_data"]
    ranked_repos = st.session_state["ranked_repos"]
    jd_analysis = st.session_state["jd_analysis"]
    latex_code = st.session_state["latex_code"]

    tab_resume, tab_projects, tab_skills, tab_latex = st.tabs(
        ["📄 Resume", "🏆 Projects", "🎯 Skills Gap", "⚙️ LaTeX"]
    )

    # ── Tab: Resume ───────────────────────────────────────────────────────────
    with tab_resume:
        st.markdown(render_resume_preview(resume_data), unsafe_allow_html=True)
        st.divider()
        # Download buttons
        col1, col2 = st.columns(2)
        col1.download_button(
            "⬇️ Download LaTeX (.tex)",
            data=latex_code,
            file_name="resume.tex",
            mime="text/plain",
            use_container_width=True,
        )
        # Markdown export
        md_lines = [
            f"# {resume_data['profile'].get('name', '')}",
            f"\n{resume_data.get('summary', '')}\n",
            "## Technical Skills",
        ]
        for cat, items in resume_data.get("skills_section", {}).items():
            if items:
                md_lines.append(f"**{cat}:** {', '.join(items)}")
        md_lines.append("\n## Projects")
        for proj in resume_data.get("projects", []):
            md_lines.append(f"\n### {proj['name']}")
            for b in proj.get("bullets", []):
                md_lines.append(f"- {b}")
        col2.download_button(
            "⬇️ Download Markdown (.md)",
            data="\n".join(md_lines),
            file_name="resume.md",
            mime="text/markdown",
            use_container_width=True,
        )

    # ── Tab: Projects ─────────────────────────────────────────────────────────
    with tab_projects:
        st.markdown("### 🏆 Ranked Projects")
        st.caption("Use Move Up / Move Down to reorder. The resume updates when you click **Apply Order**.")

        repo_order = st.session_state["repo_order"]
        ordered_repos = [ranked_repos[i] for i in repo_order if i < len(ranked_repos)]

        reorder_changed = False
        for idx, repo in enumerate(ordered_repos[:15]):
            score = repo.get("relevance_score", 0.0)
            score_pct = f"{score:.0%}"
            tags = " ".join(
                f'<span class="tag">{t}</span>'
                for t in (repo.get("topics", []) + [repo.get("language", "")])[:6]
                if t
            )
            matched = repo.get("matched_skills", [])
            matched_str = ", ".join(matched[:4]) if matched else "—"

            st.markdown(f"""
<div class="proj-card">
  <div class="proj-header">
    <span class="proj-name">#{idx+1} &nbsp; {repo['name']}</span>
    <span class="proj-score">⚡ {score_pct} match</span>
  </div>
  <div class="proj-desc">{repo.get('description', '')[:120]}</div>
  <div>{tags}</div>
  <div style="font-size:0.78rem;color:#3FB950;margin-top:6px">✓ {matched_str}</div>
</div>
""", unsafe_allow_html=True)

            c1, c2, c3 = st.columns([1, 1, 6])
            if c1.button("▲", key=f"up_{idx}") and idx > 0:
                repo_order[idx], repo_order[idx - 1] = repo_order[idx - 1], repo_order[idx]
                reorder_changed = True
            if c2.button("▼", key=f"dn_{idx}") and idx < len(ordered_repos) - 1:
                repo_order[idx], repo_order[idx + 1] = repo_order[idx + 1], repo_order[idx]
                reorder_changed = True

        if reorder_changed:
            st.session_state["repo_order"] = repo_order
            st.rerun()

        if st.button("🔄 Apply Order & Regenerate Resume", use_container_width=True):
            client = get_groq_client()
            prefs = {"pages": pages, "template": template}
            new_ranked = [ranked_repos[i] for i in repo_order]
            resume_data = rg.generate_full_resume(
                st.session_state["github_data"], new_ranked, jd_analysis, prefs, client
            )
            st.session_state["resume_data"] = resume_data
            st.session_state["latex_code"] = lg.generate_latex(resume_data, template)
            st.success("✅ Resume regenerated with new order!")
            st.rerun()

    # ── Tab: Skills Gap ───────────────────────────────────────────────────────
    with tab_skills:
        gap = resume_data.get("skill_gap", {})
        matched = gap.get("matched", [])
        missing = gap.get("missing", [])

        col_m, col_miss = st.columns(2)
        with col_m:
            st.markdown("### ✅ Skills You Have")
            st.caption(f"JD requires these — found in your GitHub")
            if matched:
                badges = " ".join(f'<span class="badge-matched">✓ {s}</span>' for s in matched)
                st.markdown(f'<div style="margin-top:8px">{badges}</div>', unsafe_allow_html=True)
            else:
                st.info("No exact matches found — check preferred skills below.")

        with col_miss:
            st.markdown("### ❌ Skills to Learn")
            st.caption("JD requires these — not found in your GitHub")
            if missing:
                badges = " ".join(f'<span class="badge-missing">✗ {s}</span>' for s in missing)
                st.markdown(f'<div style="margin-top:8px">{badges}</div>', unsafe_allow_html=True)
            else:
                st.success("🎉 You match all required skills!")

        st.divider()
        st.markdown("### 📊 JD Requirements Breakdown")
        jd_col1, jd_col2 = st.columns(2)
        with jd_col1:
            st.markdown("**Required Skills**")
            for s in jd_analysis.get("required_skills", []):
                icon = "✅" if s in matched else "❌"
                st.markdown(f"{icon} {s}")
        with jd_col2:
            st.markdown("**Preferred Skills**")
            for s in jd_analysis.get("preferred_skills", []):
                icon = "✅" if s in matched else "⚪"
                st.markdown(f"{icon} {s}")

        st.divider()
        st.markdown("### 🛠️ Your Full Tech Stack (from GitHub)")
        tech_html = " ".join(
            f'<span class="tag">{t}</span>'
            for t in sorted(gap.get("candidate_tech", []))[:40]
            if t
        )
        st.markdown(f'<div style="margin-top:8px">{tech_html}</div>', unsafe_allow_html=True)

    # ── Tab: LaTeX ────────────────────────────────────────────────────────────
    with tab_latex:
        st.markdown("### ⚙️ LaTeX Source")
        st.caption("Copy and compile with `pdflatex resume.tex` or paste into [Overleaf](https://overleaf.com).")
        st.code(latex_code, language="latex")
        col1, col2 = st.columns(2)
        col1.download_button(
            "⬇️ Download resume.tex",
            data=latex_code,
            file_name="resume.tex",
            mime="text/plain",
            use_container_width=True,
        )
        with col2:
            st.info("**Compile locally:**\n```bash\npdflatex resume.tex\n```\nOr use [Overleaf.com](https://overleaf.com) (free).")


if __name__ == "__main__":
    main()
