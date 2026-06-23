import html as html_lib
import json
import streamlit as st
from client import ResumeMCPClient
import latex

# ── Page config & global theme ──────────────────────────────────────────────
st.set_page_config(
    page_title="alldone — GitHub to Job‑Ready Resume",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)
# ── Inject custom CSS (fixed & improved) ───────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* Global overrides */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background: #0D1117;
    color: #E6EDF3;
}

/* ── Fixed topbar via native Streamlit header ── */
header[data-testid="stHeader"] {
    background: #0D1117 !important;
    border-bottom: 1px solid #30363D !important;
    height: 3.5rem !important;
    min-height: 3.5rem !important;
    z-index: 1000 !important;
}
/* BIG BOLD brand name — flat purple so ✅ emoji stays visible */
header[data-testid="stHeader"]::before {
    content: ' ✅  Alldone';
    font-family: 'Inter', sans-serif;
    font-size: 1.5rem;
    font-weight: 800;
    color: #A78BFA;
    letter-spacing: -0.5px;
    position: absolute;
    top: 50%;
    left: 4rem; /* leave room for the sidebar button at the far left */
    transform: translateY(-50%);
}
/* small italic tagline */
header[data-testid="stHeader"]::after {
    content: 'GitHub to Job-Ready Resume';
    font-family: 'Inter', sans-serif;
    font-size: 0.82rem;
    font-weight: 400;
    font-style: italic;
    color: #8B949E;
    position: absolute;
    top: 50%;
    left: 14rem;
    transform: translateY(-50%);
}

/* Hide only the hamburger menu button — keep toolbar visible for the sidebar close button */
button[data-testid="stToolbarHamburger"] { display: none !important; }

/* Make the toolbar transparent so it doesn't clash with the brand text */
[data-testid="stToolbar"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
}

/* Sidebar background */
[data-testid="stSidebar"] {
    background: #161B22;
    border-right: 1px solid #30363D;
}
/* ── Sidebar open (>) and close (X) toggle buttons ── */
[data-testid="stSidebarCollapsedControl"],
[data-testid="stSidebarCollapseButton"] {
    z-index: 10000 !important;
    opacity: 1 !important;
    visibility: visible !important;
    background: rgba(124, 58, 237, 0.25) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(124, 58, 237, 0.5) !important;
    transition: background 0.2s ease !important;
}
[data-testid="stSidebarCollapsedControl"]:hover,
[data-testid="stSidebarCollapseButton"]:hover {
    background: rgba(124, 58, 237, 0.5) !important;
}
[data-testid="stSidebarCollapsedControl"] svg,
[data-testid="stSidebarCollapseButton"] svg {
    color: #FFFFFF !important;
    fill: #FFFFFF !important;
    stroke: #FFFFFF !important;
}

/* Input card styling */
.input-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 16px;
    padding: 1.5rem 1.75rem;
    margin-bottom: 1rem;
}
.input-label {
    font-size: 0.82rem;
    font-weight: 600;
    color: #8B949E;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    margin-bottom: 0.4rem;
    display: block;
}

/* Metrics bar */
.metrics-bar {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 1rem;
    margin: 1.5rem 0;
}
.metric-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 14px;
    padding: 1.2rem 1rem;
    text-align: center;
}
.metric-value {
    font-size: 2rem;
    font-weight: 800;
    background: linear-gradient(135deg, #7C3AED, #06B6D4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}
.metric-label {
    font-size: 0.78rem;
    color: #8B949E;
    margin-top: 4px;
}

/* Score row */
.score-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.score-card {
    flex: 1;
    min-width: 120px;
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 14px;
    padding: 1rem;
    text-align: center;
}
.score-num {
    font-size: 2.4rem;
    font-weight: 800;
    line-height: 1;
}
.score-num.green  { color: #3FB950; }
.score-num.cyan   { color: #06B6D4; }
.score-num.red    { color: #F85149; }
.score-num.purple { color: #A78BFA; }
.score-sub {
    font-size: 0.75rem;
    color: #8B949E;
    margin-top: 4px;
}

/* Resume preview (white card) */
.resume-preview {
    background: #FFFFFF;
    color: #111111;
    border-radius: 12px;
    padding: 2.5rem 3rem;
    margin: 0 auto;
    box-shadow: 0 8px 40px rgba(0,0,0,0.4);
    font-size: 0.88rem;
    line-height: 1.5;
}
.resume-name {
    font-size: 2rem;
    font-weight: 700;
}
.resume-contact {
    color: #555;
    margin-bottom: 14px;
}
.resume-section-title {
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    color: #4F46E5;
    border-bottom: 2px solid #4F46E5;
    margin: 20px 0 8px;
}

/* Project cards in tab */
.proj-card {
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 14px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.85rem;
    transition: border-color 0.2s;
}
.proj-rank {
    font-size: 0.75rem;
    font-weight: 700;
    color: #8B949E;
    letter-spacing: 0.05em;
    margin-bottom: 0.3rem;
}
.proj-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.3rem;
}
.proj-stars {
    font-size: 0.8rem;
    color: #E3B341;
    background: rgba(227,179,65,0.08);
    border: 1px solid rgba(227,179,65,0.2);
    padding: 2px 10px;
    border-radius: 20px;
}
.proj-match {
    background: rgba(124,58,237,0.15);
    color: #A78BFA;
    padding: 2px 10px;
    border-radius: 20px;
    font-size: 0.8rem;
}
.tag {
    display: inline-block;
    background: #21262D;
    border: 1px solid #30363D;
    border-radius: 6px;
    padding: 2px 8px;
    font-size: 0.75rem;
    margin: 2px 2px 0 0;
    color: #8B949E;
}

/* Skill badges */
.badge-matched {
    display: inline-block;
    background: #1A3A2A;
    border: 1px solid #3FB950;
    border-radius: 8px;
    padding: 3px 10px;
    color: #3FB950;
    margin: 3px;
    font-size: 0.8rem;
}
.badge-missing {
    display: inline-block;
    background: #3A1A1A;
    border: 1px solid #F85149;
    border-radius: 8px;
    padding: 3px 10px;
    color: #F85149;
    margin: 3px;
    font-size: 0.8rem;
}
.learn-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: #161B22;
    border: 1px solid #30363D;
    border-radius: 10px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
}
.learn-skill {
    font-weight: 600;
    color: #F85149;
    min-width: 130px;
}
.learn-arrow {
    color: #8B949E;
}
.learn-tip {
    color: #8B949E;
    font-size: 0.85rem;
}

/* Buttons */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #7C3AED, #4F46E5);
    color: white;
    border: none;
    font-weight: 700;
    width: 100%;
    border-radius: 10px;
    font-size: 1rem;
    padding: 0.65rem;
    transition: opacity 0.2s;
    box-shadow: 0 2px 8px rgba(124,58,237,0.3);
}
div[data-testid="stButton"] > button:hover {
    opacity: 0.9;
}

/* Section divider */
.section-divider {
    height: 1px;
    background: #21262D;
    margin: 1.5rem 0;
}

/* Spinner overrides */
.stSpinner > div {
    border-color: #A78BFA transparent transparent transparent !important;
}
/* Style multiselect dropdown */
div[data-baseweb="select"] {
    background: #161B22;
    border: 1px solid #30363D !important;
    border-radius: 10px !important;
}
div[data-baseweb="select"] * {
    font-family: 'Inter', sans-serif !important;
    color: #E6EDF3 !important;
}
div[data-baseweb="popover"] {
    background: #161B22 !important;
    border: 1px solid #30363D !important;
}
</style>
""",
    unsafe_allow_html=True,
)


# ── Session state init (improved reset logic) ──────────────────────────────
INITIAL_STATE = {
    "generated": False,
    "github_data": None,
    "jd_analysis": None,
    "ranked_repos": None,
    "skill_gap": None,
    "resume_data": None,
    "latex_code": None,
    "repo_order": None,
    "error": None,
    "selection_ready": False,
    "selected_repo_indices": [],
}

# If any key missing or "generated" not set, init all
if "generated" not in st.session_state:
    st.session_state.update(INITIAL_STATE)

# ── Sidebar ─────────────────────────────────────────────────────────────────
# ── Sidebar settings ──────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Settings")
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)

    st.markdown("<span class='input-label'>Resume Length</span>", unsafe_allow_html=True)
    length_choice = st.radio(
        "Length", options=["1 Page", "2 Pages"],
        label_visibility="collapsed", horizontal=True,
    )
    pages = int(length_choice[0])

    st.markdown("<span class='input-label'>Project Ranking</span>", unsafe_allow_html=True)
    ranking = st.radio(
        "Ranking", ["JD Relevance", "Popularity"],
        label_visibility="collapsed", horizontal=True,
    )

    st.markdown("<span class='input-label'>LLM Provider</span>", unsafe_allow_html=True)
    model_choice = st.selectbox(
        "LLM Provider",
        ["Groq (Llama 3.3 70B)", "Google (Gemini 1.5 Pro)"],
        index=0, label_visibility="collapsed",
    )

    st.markdown("<span class='input-label'>Number of Projects in Resume</span>", unsafe_allow_html=True)
    num_projects = st.slider(
        "Projects", min_value=1, max_value=5, value=3,
        label_visibility="collapsed",
        help="How many projects to include in the resume (1–5)"
    )

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    if st.button("🔄 Reset All", use_container_width=True):
        st.session_state.clear()
        st.session_state.update(INITIAL_STATE)
        st.rerun()

# ── Main input form ───────────────────────────────────────────────────────────
with st.container():
    username = st.text_input(
        "GitHub Username",
        placeholder="e.g. torvalds",
        label_visibility="visible",
    )
    jd_text = st.text_area(
        "Job Description",
        height=220,
        placeholder="Paste the full job description here. The AI will match your GitHub projects to it.",
    )

    with st.expander("✏️ Custom Instructions  (optional)", expanded=False):
        user_instructions = st.text_area(
            "Instructions",
            height=120,
            placeholder=(
                "Tell the AI how to tailor your resume.\n"
                "Examples:\n"
                "• Focus on backend and system-design projects\n"
                "• Keep the tone formal and concise\n"
                "• Highlight open-source contributions\n"
                "• Omit projects older than 2022"
            ),
            label_visibility="collapsed",
        )

    col_btn, col_err = st.columns([1, 2])
    with col_btn:
        generate = st.button("🚀 Generate Resume", use_container_width=True)
    with col_err:
        if st.session_state.error:
            st.error(st.session_state.error)

# ── Pipeline execution ─────────────────────────────────────────────────────
if generate:
    if not username or not jd_text:
        st.warning("Please enter your GitHub username and paste a job description.")
        st.stop()

    try:
        # ── Phase 1: fetch, analyse, rank ──
        with st.status("🚀 Running Pipeline...", expanded=True) as status:
            with st.spinner("Initializing client..."):
                mcp = ResumeMCPClient()

            st.write("🔍 Extracting GitHub profile ...")
            gh_data = mcp.call("extract_github_profile", {"username": username})
            st.session_state.github_data = gh_data

            st.write("🧠 Analyzing Candidate & Job Description...")
            analysis_res = mcp.call("analyze_candidate", {
                "github_data_json": json.dumps(gh_data),
                "jd_text": jd_text,
                "prefs_json": json.dumps({"model_choice": model_choice}),
            })
            
            # The tool returns {"jd_analysis": ..., "ranked_repos": ..., "skill_gap": ...}
            st.session_state.jd_analysis = analysis_res.get("jd_analysis", {})
            st.session_state.skill_gap = analysis_res.get("skill_gap", {"matched": [], "missing": []})
            
            ranked = analysis_res.get("ranked_repos", [])
            # Re-sort if user prefers Popularity ranking over JD Relevance
            if ranking == "Popularity":
                ranked = sorted(
                    ranked,
                    key=lambda x: x.get("stargazers_count", 0),
                    reverse=True,
                )
            
            st.session_state.ranked_repos = ranked
            st.session_state.repo_order = list(range(len(ranked)))
            st.session_state.selection_ready = True   # <-- trigger selection UI
            st.session_state.error = None
            status.update(label="✅ Ranking done. Choose your projects below.", state="complete")

    except Exception as e:
        st.session_state.error = str(e)
        st.error(f"Error: {e}")
        st.stop()

# ── Phase 2: project selection UI (shown after ranking) ──
if st.session_state.get("selection_ready") and not st.session_state.get("generated"):
    st.markdown("## 🏆 Select Projects for Your Resume (max 5)")
    ranked_repos = st.session_state.ranked_repos

    # Create a multiselect with project names and default to top 5
    repo_options = [
        f"{i+1}. {r['name']} (match: {r.get('relevance_score',0):.0%})"
        for i, r in enumerate(ranked_repos[:15])   # show top 15 for choice
    ]
    default_selection = repo_options[:5]   # pre‑select first 5

    selected_labels = st.multiselect(
        "Choose the projects you want to include:",
        options=repo_options,
        default=default_selection,
        max_selections=5,
        key="project_selector"
    )

    # Map selected labels back to indices in `ranked_repos`
    selected_indices = [
        repo_options.index(label) for label in selected_labels
    ]
    st.session_state.selected_repo_indices = selected_indices

    # Confirm button to finalise the resume
    if st.button("✅ Generate Resume with Selected Projects", use_container_width=True):
        if not selected_indices:
            st.warning("Please select at least one project.")
            st.stop()

        try:
            with st.status("✍️ Generating final resume...", expanded=True) as status:
                mcp = ResumeMCPClient()   # re‑instantiate or reuse from before if possible

                # Build the filtered repo list
                final_ranked = [ranked_repos[i] for i in selected_indices]

                st.write("✍️ Generating resume content...")
                prefs = {
                    "pages": pages,
                    "num_projects": num_projects,
                    "template": "ATS Classic",
                    "user_instructions": user_instructions or "",
                    "model_choice": model_choice,
                }
                resume_data = mcp.call("generate_resume_content", {
                    "github_data_json": json.dumps(st.session_state.github_data),
                    "ranked_repos_json": json.dumps(final_ranked),
                    "jd_analysis_json": json.dumps(st.session_state.jd_analysis),
                    "prefs_json": json.dumps(prefs),
                    "skill_gap_json": json.dumps(st.session_state.skill_gap),
                })
                st.session_state.resume_data = resume_data

                st.write("📄 Building LaTeX...")
                st.session_state.latex_code = latex.generate_latex(resume_data, "ATS Classic")

                st.session_state.generated = True
                st.session_state.selection_ready = False   # hide selection UI
                st.session_state.error = None
                status.update(label="✅ Resume ready!", state="complete")
                st.rerun()

        except Exception as e:
            st.session_state.error = str(e)
            st.error(f"Error: {e}")
            st.stop()

# ── Results display ─────────────────────────────────────────────────────────
if st.session_state.generated:
    data = st.session_state.resume_data
    ranked = st.session_state.ranked_repos
    gap = data.get("skill_gap", {})
    matched_sk = gap.get("matched", [])
    missing_sk = gap.get("missing", [])

    total_repos = len(ranked)
    top_score = ranked[0].get("relevance_score", 0) if ranked else 0
    skills_total = len(matched_sk) + len(missing_sk)
    skills_matched = len(matched_sk)

    # ── Metrics bar ──
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    st.markdown(
        f"""
        <div class="metrics-bar">
            <div class="metric-card">
                <div class="metric-value">{total_repos}</div>
                <div class="metric-label">Projects Analyzed</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{top_score:.0%}</div>
                <div class="metric-label">Top Project Match</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{skills_matched}/{skills_total if skills_total else '?'}</div>
                <div class="metric-label">Skills Matched</div>
            </div>
            <div class="metric-card">
                <div class="metric-value">{data.get('pages', pages)}pg</div>
                <div class="metric-label">Resume Length</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    t1, t2, t3, t4 = st.tabs(["📄 Resume", "🏆 Projects", "🎯 Skill Gap", "⚙️ LaTeX"])

    # ── Tab 1: Resume ─────────────────────────────────────────────────────
    with t1:
        skills_pct = int((skills_matched / skills_total * 100)) if skills_total else 0
        jd_match_pct = int(top_score * 100) if top_score else skills_pct
        ats_score = min(99, int(skills_pct * 0.5 + jd_match_pct * 0.4 + 10))
        missing_count = len(missing_sk)

        st.markdown(
            f"""
            <div class="score-row">
                <div class="score-card">
                    <div class="score-num green">{ats_score}</div>
                    <div class="score-sub">ATS Score</div>
                </div>
                <div class="score-card">
                    <div class="score-num cyan">{jd_match_pct}%</div>
                    <div class="score-sub">JD Match</div>
                </div>
                <div class="score-card">
                    <div class="score-num red">{missing_count}</div>
                    <div class="score-sub">Missing Skills</div>
                </div>
                <div class="score-card">
                    <div class="score-num purple">{skills_matched}</div>
                    <div class="score-sub">Skills Matched</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Build resume preview HTML
        p = data["profile"]
        name = p.get("name") or p.get("username", "")
        email = p.get("email", "")
        gh_url = p.get("html_url", "")
        location = p.get("location", "")
        blog = p.get("blog", "")

        contacts = []
        if location:
            contacts.append(location)
        if email:
            contacts.append(
                f'<a href="mailto:{email}" style="color:#4F46E5">{email}</a>'
            )
        if gh_url:
            contacts.append(
                f'<a href="{gh_url}" style="color:#4F46E5" target="_blank">⭐ GitHub</a>'
            )
        if blog:
            blog_link = blog if blog.startswith("http") else f"https://{blog}"
            contacts.append(
                f'<a href="{blog_link}" style="color:#4F46E5" target="_blank">🔗 Portfolio/LinkedIn</a>'
            )

        html = "<div class='resume-preview'>"
        html += f"<div class='resume-name'>{name}</div>"
        html += f"<div class='resume-contact'>{'  |  '.join(contacts) if contacts else ''}</div>"

        if data.get("summary"):
            html += f"<div class='resume-section-title'>Summary</div><div style='margin-bottom:8px'>{data['summary']}</div>"

        if skills_section := data.get("skills_section"):
            html += "<div class='resume-section-title'>Technical Skills</div>"
            for cat, items in skills_section.items():
                if items:
                    clean_items = [str(i) for i in items if i]
                    html += f"<div style='margin-bottom:4px'><strong>{cat}:</strong> {', '.join(clean_items)}</div>"

        html += "<div class='resume-section-title'>Projects</div>"
        for proj in data.get("projects", []):
            repo_url = proj.get("html_url") or proj.get("url", "")
            tech = ", ".join(proj.get("tech_stack", [])[:5])
            one_liner = proj.get("one_liner") or proj.get("description", "")
            if repo_url:
                proj_header = (
                    f'<a href="{repo_url}" target="_blank" '
                    f'style="color:#4F46E5;font-weight:700;text-decoration:none">'
                    f'{proj["name"]}</a>'
                    f' &nbsp;<a href="{repo_url}" target="_blank" '
                    f'style="color:#4F46E5;font-size:0.85rem">↗ GitHub</a>'
                )
            else:
                proj_header = f'<strong>{proj["name"]}</strong>'

            html += "<div style='margin-bottom:12px'>"
            html += (
                f"<div style='display:flex;justify-content:space-between;align-items:baseline'>"
                f"{proj_header}"
                f"<span style='color:#666;font-size:0.8rem'>{tech}</span>"
                f"</div>"
            )
            if one_liner:
                html += (
                    f"<div style='color:#555;font-style:italic;font-size:0.82rem;"
                    f"margin:2px 0 4px'>{one_liner}</div>"
                )
            for bullet in proj.get("bullets", []):
                html += f"<div style='margin-left:12px'>• {bullet}</div>"
            html += "</div>"

        if contributions := data.get("contributions", []):
            html += "<div class='resume-section-title'>Open Source Contributions</div>"
            for contrib in contributions:
                url = contrib.get("url", "")
                cname = contrib.get("name", "Project")
                desc = contrib.get("contribution", "")
                if url:
                    header = (
                        f"<a href='{url}' target='_blank' "
                        f"style='color:#4F46E5;font-weight:700;text-decoration:none'>{cname}</a>"
                    )
                else:
                    header = f"<strong>{cname}</strong>"
                html += f"<div style='margin-bottom:6px'>• {header}: {desc}</div>"

        html += "</div>"

        st.markdown(html, unsafe_allow_html=True)
        st.download_button(
            label="⬇️ Download .tex",
            data=st.session_state.latex_code,
            file_name="resume.tex",
            mime="text/plain",
            use_container_width=True,
        )

    # ── Tab 2: Projects ───────────────────────────────────────────────────
    with t2:
        for position, idx in enumerate(st.session_state.repo_order[:15], start=1):
            r = ranked[idx]
            repo_url = r.get("html_url", "")
            safe_name = html_lib.escape(r["name"])
            name_html = (
                f'<a href="{repo_url}" target="_blank" '
                f'style="color:#A78BFA;font-weight:700;font-size:1rem">{safe_name}</a>'
                if repo_url
                else f'<strong style="font-size:1rem">{safe_name}</strong>'
            )
            score_pct = r.get("relevance_score", 0)
            stars = r.get("stargazers_count", 0)
            desc = html_lib.escape((r.get("description") or "")[:140])
            tech_tags = r.get("tech_stack") or r.get("topics", [])
            matched = r.get("matched_skills", [])[:4]

            tags_html = " ".join(
                f"<span class='tag'>{html_lib.escape(str(t))}</span>" for t in tech_tags[:6]
            )
            matched_html = " ".join(
                f"<span class='badge-matched'>✓ {html_lib.escape(str(s))}</span>" for s in matched
            )
            stars_html = f"<span class='proj-stars'>⭐ {stars:,}</span>" if stars else ""

            card = (
                f'<div class="proj-card">'
                f'<div class="proj-rank">#{position}</div>'
                f'<div class="proj-header">'
                f'{name_html}'
                f'<div style="display:flex;gap:6px;align-items:center">'
                f'{stars_html}'
                f'<span class="proj-match">⚡ {score_pct:.0%} match</span>'
                f'</div></div>'
                f'<div style="color:#8B949E;font-size:0.85rem;margin:4px 0 8px">{desc}</div>'
                f'<div style="margin-bottom:6px">{tags_html}</div>'
                f'<div>{matched_html}</div>'
                f'</div>'
            )
            st.markdown(card, unsafe_allow_html=True)


    # ── Tab 3: Skill Gap ──────────────────────────────────────────────────
    with t3:
        LEARN_TIPS = {
            "aws": "Add a cloud deployment project (e.g., host an app on EC2 or Lambda)",
            "kubernetes": "Deploy a containerized app with K8s locally using Minikube",
            "docker": "Containerize one of your existing GitHub projects",
            "terraform": "Write IaC for a small cloud project",
            "graphql": "Add a GraphQL API to an existing backend project",
            "typescript": "Migrate one JS project to TypeScript",
            "rust": "Build a small CLI tool in Rust",
            "go": "Build a REST API or CLI tool in Go",
            "postgres": "Add a PostgreSQL backend to a personal project",
            "redis": "Implement caching with Redis in an existing app",
            "ci/cd": "Set up GitHub Actions for a project",
            "testing": "Add unit tests with pytest or jest to a project",
        }

        col_a, col_b = st.columns(2)
        with col_a:
            st.markdown("### ✅ Matched Skills")
            matched_badges = " ".join(
                f"<span class='badge-matched'>✓ {s}</span>" for s in matched_sk
            )
            st.markdown(
                matched_badges if matched_badges else "_None matched_",
                unsafe_allow_html=True,
            )
        with col_b:
            st.markdown("### ❌ Missing Skills")
            missing_badges = " ".join(
                f"<span class='badge-missing'>✗ {s}</span>" for s in missing_sk
            )
            st.markdown(
                missing_badges if missing_badges else "_No gaps detected_",
                unsafe_allow_html=True,
            )

        if missing_sk:
            st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
            st.markdown("### 📚 Recommended Learning")
            for skill in missing_sk:
                tip = LEARN_TIPS.get(skill.lower(), f"Build a project that demonstrates {skill}")
                st.markdown(
                    f"""<div class="learn-row">
                        <div class="learn-skill">{skill}</div>
                        <div class="learn-arrow">→</div>
                        <div class="learn-tip">{tip}</div>
                    </div>""",
                    unsafe_allow_html=True,
                )

    # ── Tab 4: LaTeX ──────────────────────────────────────────────────────
    with t4:
        st.code(st.session_state.latex_code, language="latex")