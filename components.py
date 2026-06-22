"""
components.py — Reusable Streamlit UI components for GitHub Resume Parser.

Each function renders a self-contained section of the UI.
"""

import streamlit as st
from typing import Any


# ── Sidebar ───────────────────────────────────────────────────────────────────

def render_sidebar() -> tuple[str, int, str, str]:
    """
    Render the settings sidebar.

    Returns:
        (username, pages, template, ranking_mode)
    """
    with st.sidebar:
        st.markdown("## 🎯 Resume Settings")
        st.divider()

        st.markdown('<div class="sidebar-label">GitHub Username</div>', unsafe_allow_html=True)
        username = st.text_input(
            "GitHub Username",
            placeholder="e.g. torvalds",
            key="username",
            label_visibility="collapsed",
        )

        st.markdown('<div class="sidebar-label">Resume Length</div>', unsafe_allow_html=True)
        pages = st.radio(
            "Resume Length",
            ["1 Page", "2 Pages"],
            key="pages",
            label_visibility="collapsed",
        )

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
            for k in ["generated", "github_data", "jd_analysis",
                      "ranked_repos", "resume_data", "latex_code", "repo_order", "error"]:
                st.session_state[k] = False if k == "generated" else None
            st.rerun()

        _render_profile_card()

    return username, int(pages[0]), template, ranking


def _render_profile_card() -> None:
    """Show avatar + stats after profile is fetched."""
    github_data = st.session_state.get("github_data")
    if not github_data:
        return
    p = github_data["profile"]
    st.divider()
    if p.get("avatar_url"):
        st.image(p["avatar_url"], width=80)
    st.markdown(f"**{p.get('name', p.get('username', ''))}**")
    if p.get("bio"):
        st.caption(p["bio"])
    col1, col2 = st.columns(2)
    col1.metric("⭐ Stars", github_data.get("total_stars", 0))
    col2.metric("📦 Repos", p.get("public_repos", 0))


# ── Hero ──────────────────────────────────────────────────────────────────────

def render_hero() -> None:
    """Render the gradient hero header."""
    st.markdown("""
<div class="hero">
  <h1>🎯 GitHub Resume Parser</h1>
  <p>JD → GitHub → ATS Resume &nbsp;·&nbsp; Powered by Groq LLM</p>
</div>
""", unsafe_allow_html=True)


# ── Empty state ───────────────────────────────────────────────────────────────

def render_empty_state() -> None:
    """Placeholder shown before any resume is generated."""
    st.markdown("""
<div style="text-align:center;padding:4rem 0;color:#8B949E">
  <div style="font-size:4rem">🚀</div>
  <div style="font-size:1.1rem;margin-top:0.5rem">
    Enter your GitHub username, paste a job description,<br>
    and click <strong>Generate Resume</strong>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Resume tab ────────────────────────────────────────────────────────────────

def render_resume_tab(resume_data: dict[str, Any], latex_code: str) -> None:
    """Render the Resume preview tab with download buttons."""
    st.markdown(build_resume_html(resume_data), unsafe_allow_html=True)
    st.divider()

    col1, col2 = st.columns(2)
    col1.download_button(
        "⬇️ Download LaTeX (.tex)",
        data=latex_code,
        file_name="resume.tex",
        mime="text/plain",
        use_container_width=True,
    )
    col2.download_button(
        "⬇️ Download Markdown (.md)",
        data=build_resume_markdown(resume_data),
        file_name="resume.md",
        mime="text/markdown",
        use_container_width=True,
    )


def build_resume_html(data: dict[str, Any]) -> str:
    """Build an HTML string for the white-paper resume preview."""
    profile = data["profile"]
    name = profile.get("name", profile.get("username", ""))
    email = profile.get("email", "")
    github_url = profile.get("html_url", "")
    location = profile.get("location", "")
    blog = profile.get("blog", "")

    contact_parts: list[str] = []
    if location:
        contact_parts.append(location)
    if email:
        contact_parts.append(f'<a href="mailto:{email}" style="color:#4F46E5">{email}</a>')
    if github_url:
        contact_parts.append(f'<a href="{github_url}" style="color:#4F46E5">GitHub</a>')
    if blog:
        blog_url = blog if blog.startswith("http") else f"https://{blog}"
        contact_parts.append(f'<a href="{blog_url}" style="color:#4F46E5">Portfolio</a>')

    html = f'<div class="resume-preview">'
    html += f'<div class="resume-name">{name}</div>'
    html += f'<div class="resume-contact">{" &nbsp;|&nbsp; ".join(contact_parts)}</div>'

    if summary := data.get("summary"):
        html += '<div class="resume-section-title">Professional Summary</div>'
        html += f'<div class="resume-summary">{summary}</div>'

    if skills := data.get("skills_section"):
        html += '<div class="resume-section-title">Technical Skills</div>'
        for cat, items in skills.items():
            if items:
                html += f'<div style="margin-bottom:5px"><strong>{cat}:</strong> {", ".join(items)}</div>'

    if projects := data.get("projects"):
        html += '<div class="resume-section-title">Projects</div>'
        for proj in projects:
            tech = " · ".join(proj.get("tech_stack", [])[:5])
            url = proj.get("url", "")
            name_part = (
                f'<a href="{url}" style="color:#4F46E5;font-weight:600">{proj["name"]}</a>'
                if url else
                f'<span class="resume-proj-name">{proj["name"]}</span>'
            )
            bullets_html = "".join(
                f'<div class="resume-bullet">• {b}</div>'
                for b in proj.get("bullets", [])
            )
            html += f'<div style="margin-bottom:12px">'
            html += f'<div>{name_part} <span class="resume-proj-tech">| {tech}</span></div>'
            html += bullets_html
            html += '</div>'

    html += "</div>"
    return html


def build_resume_markdown(data: dict[str, Any]) -> str:
    """Build a Markdown string of the resume for download."""
    lines: list[str] = []
    profile = data["profile"]
    lines.append(f"# {profile.get('name', profile.get('username', ''))}")
    lines.append("")

    contacts = []
    if profile.get("email"):
        contacts.append(profile["email"])
    if profile.get("html_url"):
        contacts.append(profile["html_url"])
    if profile.get("blog"):
        contacts.append(profile["blog"])
    if contacts:
        lines.append(" | ".join(contacts))
        lines.append("")

    if summary := data.get("summary"):
        lines += ["## Summary", summary, ""]

    if skills := data.get("skills_section"):
        lines.append("## Technical Skills")
        for cat, items in skills.items():
            if items:
                lines.append(f"**{cat}:** {', '.join(items)}")
        lines.append("")

    if projects := data.get("projects"):
        lines.append("## Projects")
        for proj in projects:
            lines.append(f"\n### {proj['name']}")
            if proj.get("url"):
                lines.append(f"[GitHub]({proj['url']})")
            for b in proj.get("bullets", []):
                lines.append(f"- {b}")

    return "\n".join(lines)


# ── Projects tab ──────────────────────────────────────────────────────────────

def render_projects_tab(
    ranked_repos: list[dict[str, Any]],
    pages: int,
    template: str,
    jd_analysis: dict[str, Any],
) -> None:
    """Render the Projects ranking tab with reorder controls."""
    st.markdown("### 🏆 Ranked Projects")
    st.caption("Use ▲ / ▼ to reorder. Click **Apply Order & Regenerate** to rebuild the resume.")

    repo_order: list[int] = st.session_state["repo_order"]
    ordered_repos = [ranked_repos[i] for i in repo_order if i < len(ranked_repos)]

    reorder_changed = False
    for idx, repo in enumerate(ordered_repos[:15]):
        _render_project_card(idx, repo)

        c1, c2, _ = st.columns([1, 1, 8])
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
        _regenerate_with_order(ranked_repos, repo_order, jd_analysis, pages, template)


def _render_project_card(idx: int, repo: dict[str, Any]) -> None:
    """Render a single project card HTML block."""
    score = repo.get("relevance_score", 0.0)
    score_pct = f"{score:.0%}"
    all_tags = repo.get("topics", []) + ([repo.get("language", "")] if repo.get("language") else [])
    tags_html = " ".join(f'<span class="tag">{t}</span>' for t in all_tags[:6])
    matched = repo.get("matched_skills", [])
    matched_str = ", ".join(matched[:4]) if matched else "—"
    desc = (repo.get("description") or "")[:120]
    stars = repo.get("stargazers_count", 0)

    st.markdown(f"""
<div class="proj-card">
  <div class="proj-header">
    <span class="proj-name">#{idx + 1} &nbsp; {repo['name']}
      {"&nbsp; ⭐ " + str(stars) if stars else ""}
    </span>
    <span class="proj-score">⚡ {score_pct} match</span>
  </div>
  <div class="proj-desc">{desc}</div>
  <div>{tags_html}</div>
  <div style="font-size:0.78rem;color:#3FB950;margin-top:6px">✓ {matched_str}</div>
</div>
""", unsafe_allow_html=True)


def _regenerate_with_order(
    ranked_repos: list[dict[str, Any]],
    repo_order: list[int],
    jd_analysis: dict[str, Any],
    pages: int,
    template: str,
) -> None:
    """Regenerate resume and LaTeX with the user's custom project order."""
    import resume_generator as rg
    import latex_generator as lg
    from utils import get_groq_client

    client = get_groq_client()
    prefs = {"pages": pages, "template": template}
    new_ranked = [ranked_repos[i] for i in repo_order]
    resume_data = rg.generate_full_resume(
        st.session_state["github_data"], new_ranked, jd_analysis, prefs, client
    )
    st.session_state["resume_data"] = resume_data
    st.session_state["latex_code"] = lg.generate_latex(resume_data, template)
    st.success("✅ Resume regenerated with your project order!")
    st.rerun()


# ── Skills Gap tab ────────────────────────────────────────────────────────────

def render_skills_tab(
    resume_data: dict[str, Any],
    jd_analysis: dict[str, Any],
) -> None:
    """Render the Skills Gap analysis tab."""
    gap = resume_data.get("skill_gap", {})
    matched = gap.get("matched", [])
    missing = gap.get("missing", [])

    col_m, col_miss = st.columns(2)

    with col_m:
        st.markdown("### ✅ Skills You Have")
        st.caption("JD requires these — found in your GitHub")
        if matched:
            badges = " ".join(f'<span class="badge-matched">✓ {s}</span>' for s in matched)
            st.markdown(f'<div style="margin-top:8px">{badges}</div>', unsafe_allow_html=True)
        else:
            st.info("No exact matches found — check preferred skills below.")

    with col_miss:
        st.markdown("### ❌ Skills to Learn")
        st.caption("JD requires these — not evidenced in your GitHub")
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
            st.markdown(f'{"✅" if s in matched else "❌"} {s}')
    with jd_col2:
        st.markdown("**Preferred Skills**")
        for s in jd_analysis.get("preferred_skills", []):
            st.markdown(f'{"✅" if s in matched else "⚪"} {s}')

    st.divider()
    st.markdown("### 🛠️ Your Full Tech Stack (from GitHub)")
    tech_html = " ".join(
        f'<span class="tag">{t}</span>'
        for t in sorted(gap.get("candidate_tech", []))[:40]
        if t
    )
    st.markdown(f'<div style="margin-top:8px">{tech_html}</div>', unsafe_allow_html=True)


# ── LaTeX tab ─────────────────────────────────────────────────────────────────

def render_latex_tab(latex_code: str) -> None:
    """Render the LaTeX source viewer tab."""
    st.markdown("### ⚙️ LaTeX Source")
    st.caption("Compile with `pdflatex resume.tex` or paste into [Overleaf](https://overleaf.com).")
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
        st.markdown("""
**Compile locally:**
```bash
pdflatex resume.tex
```
Or upload to [Overleaf.com](https://overleaf.com) *(free)*.
""")
