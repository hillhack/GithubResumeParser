import os
import streamlit as st
from pathlib import Path
from tools import extract_jd_skills_tool, analyse_repos_tool, generate_resume_tool
from github_api import fetch_github_repos
from cache import cache_stats, clear_namespace
import latex

# ── .env ─────────────────────────────────────────────────────────────────────
if Path(".env").exists():
    for line in Path(".env").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ[k.strip()] = v.strip()

st.set_page_config(
    page_title="Alldone — AI Resume Builder",
    page_icon="✅",
    layout="centered",
    initial_sidebar_state="expanded",
)

# ── CSS: sticky top bar + clean inputs ───────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }

/* Hide only the top boundary decoration */
[data-testid="stDecoration"] { display: none; }

/* Hide the Streamlit header background to let our UI shine, but keep it functional */
header[data-testid="stHeader"] { 
    background: transparent !important; 
    box-shadow: none !important; 
}

/* Ensure the main container has space for our topbar */
.main .block-container { padding-top: 1rem !important; padding-bottom: 3rem; max-width: 760px; }

/* ── Modern SaaS Topbar ── */
.topbar-container {
    position: sticky;
    top: 1rem;
    z-index: 999;
    background: #0e0e1a;
    border: 1px solid #1e1e35;
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 30px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.2);
}
.topbar-logo { font-size: 1.6rem; font-weight: 800; color: #a78bfa; letter-spacing: -0.5px; display: flex; align-items: center; gap: 8px; }
.topbar-logo span { 
    background: #4ade80; color: #000; border-radius: 6px; 
    padding: 2px 7px; font-size: 1.1rem;
}
.topbar-sub { color: #94a3b8; font-size: 1rem; font-weight: 500; border-left: 2px solid #2d2d50; padding-left: 16px; }
.topbar-divider { flex: 1; }
.topbar-pill {
    background: #1e1e35; color: #a78bfa;
    border-radius: 20px; padding: 6px 16px;
    font-size: 0.8rem; font-weight: 600;
    border: 1px solid #2d2d50;
}

/* ── Section labels ── */
.slabel {
    font-size: 0.72rem; font-weight: 700; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 0.08em;
    margin: 1.4rem 0 0.35rem; display: block;
}

/* ── Inputs ── */
.stTextInput input, .stTextArea textarea {
    background: #13131f !important; border: 1px solid #2a2a45 !important;
    border-radius: 8px !important; color: #e2e8f0 !important;
    font-size: 0.95rem !important;
}
.stTextInput input::placeholder, .stTextArea textarea::placeholder { color: #4b5563 !important; }
.stTextInput input:focus, .stTextArea textarea:focus {
    border-color: #7c3aed !important;
    box-shadow: 0 0 0 2px rgba(124,58,237,0.2) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: linear-gradient(135deg, #6d28d9, #7c3aed) !important;
    color: white !important; border: none !important;
    border-radius: 9px !important; font-weight: 700 !important;
    font-size: 0.95rem !important; padding: 0.55rem 1.4rem !important;
    box-shadow: 0 4px 14px rgba(109,40,217,0.4) !important;
    transition: all 0.2s !important;
}
.stButton > button:hover { box-shadow: 0 6px 20px rgba(109,40,217,0.55) !important; }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background: transparent; border-bottom: 1px solid #1e1e35; gap: 4px; }
.stTabs [data-baseweb="tab"] { color: #6b7280; font-weight: 600; padding: 0.5rem 1rem; border-radius: 6px 6px 0 0; }
.stTabs [aria-selected="true"] { color: #a78bfa !important; border-bottom: 2px solid #7c3aed; background: #13131f !important; }

/* ── Radio ── */
.stRadio [data-testid="stMarkdownContainer"] p { color: #cbd5e1; }
.stRadio label { color: #cbd5e1 !important; font-size: 0.92rem; }

/* ── Sidebar ── */
[data-testid="stSidebar"] { background: #0a0a14 !important; border-right: 1px solid #1a1a2e; }
[data-testid="stSidebar"] * { color: #cbd5e1 !important; }
[data-testid="stSidebar"] .stSelectbox > label { font-size: 0.75rem; color: #6b7280 !important; font-weight: 600; text-transform: uppercase; }

/* ── Expander ── */
.streamlit-expanderHeader { color: #94a3b8 !important; font-size: 0.85rem !important; }

/* ── Skill pills ── */
.pill-ok  { display:inline-block; background:#052e16; color:#4ade80; border:1px solid #166534; border-radius:20px; padding:2px 10px; font-size:0.75rem; font-weight:600; margin:2px; }
.pill-no  { display:inline-block; background:#2d0a0a; color:#f87171; border:1px solid #7f1d1d; border-radius:20px; padding:2px 10px; font-size:0.75rem; font-weight:600; margin:2px; }

/* ── Checkbox ── */
.stCheckbox label { color: #cbd5e1 !important; font-size: 0.88rem !important; }

/* ── Metric ── */
[data-testid="stMetricValue"] { color: #a78bfa !important; font-weight: 700 !important; }
</style>

<!-- Modern SaaS Topbar -->
<div class="topbar-container">
  <div class="topbar-logo"><span>✅</span>Alldone</div>
  <div class="topbar-sub">GitHub → Job Ready Resume</div>
  <div class="topbar-divider"></div>
  <div class="topbar-pill">AI Resume Builder</div>
</div>
""", unsafe_allow_html=True)

# ── Error helper ──────────────────────────────────────────────────────────────
def handle_error(e):
    msg = str(e).lower()
    if "429" in msg or "quota" in msg:
        st.error("🚨 Rate limit hit. Wait or switch API key.")
    else:
        st.error(f"🚨 {e}")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Settings")
    max_projects = st.slider("Max Projects in Resume", 1, 6, 3)
    resume_length = st.radio("Resume Length", ["1 Page", "2 Pages"], horizontal=True)
    
    provider = st.selectbox("Provider", ["Groq", "Gemini", "HuggingFace"])
    if provider == "Groq":
        api_key = st.text_input("Groq API Key", type="password", value=os.environ.get("GROQ_API_KEY", ""))
        model   = st.selectbox("Model", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"])
    elif provider == "Gemini":
        api_key = st.text_input("Gemini API Key", type="password", value=os.environ.get("GEMINI_API_KEY", ""))
        model   = st.selectbox("Model", ["gemini-1.5-flash", "gemini-1.5-pro"])
    else:
        api_key = st.text_input("HuggingFace Token", type="password", value=os.environ.get("HF_TOKEN", ""))
        model   = st.selectbox("Model", ["mistralai/Mixtral-8x7B-Instruct-v0.1"])

    github_token = st.text_input(
        "GitHub Token (optional)",
        type="password",
        value=os.environ.get("GITHUB_TOKEN", ""),
        help="Raises API limit from 60 → 5,000 req/hr. Get one at github.com/settings/tokens",
        placeholder="ghp_..."
    )
    if github_token:
        os.environ["GITHUB_TOKEN"] = github_token

    stats = cache_stats()
    st.caption(f"🗄️ Cache: {stats['files']} files · {stats['size_kb']} KB")
    if st.button("🗑️ Clear Cache", use_container_width=True):
        clear_namespace("github_repos")
        clear_namespace("github_enrich")
        st.success("Cache cleared!")
        st.rerun()

# ── Pipeline ──────────────────────────────────────────────────────────────────
def run_pipeline(username, repos, jd_text, instructions):
    with st.status("⏳ Running pipeline…", expanded=True) as status:
        try:
            if provider == "Groq":        os.environ["GROQ_API_KEY"]   = api_key
            elif provider == "Gemini":    os.environ["GEMINI_API_KEY"] = api_key
            else:                         os.environ["HF_TOKEN"]       = api_key

            st.write("Step 1 — Extracting JD skills…")
            jd_data = extract_jd_skills_tool(jd_text, provider, model)

            st.write(f"Step 2 — Analysing {len(repos)} repositories…")
            matches = analyse_repos_tool(repos, jd_data, username, provider, model)

            st.write("Step 3 — Generating resume…")
            length_instruction = f"IMPORTANT: Format the resume strictly to fit {resume_length}. Keep descriptions concise if 1 Page."
            final_instructions = f"{length_instruction}\n{instructions}" if instructions else length_instruction
            resume  = generate_resume_tool(username, matches[:max_projects], jd_data, final_instructions, provider, model)
            tex     = latex.generate_latex(resume)

            st.session_state.update(
                resume_data=resume, latex_code=tex,
                match_results=matches, jd_profile=jd_data
            )
            status.update(label="✅ Resume ready! See below.", state="complete")
        except Exception as e:
            status.update(label="❌ Failed", state="error")
            handle_error(e)

# ── Input form ────────────────────────────────────────────────────────────────
st.markdown('<span class="slabel">ANALYSIS MODE</span>', unsafe_allow_html=True)
mode = st.radio("mode", ["Full Analysis (Scan all repositories)", "Quick Analysis (Select Repositories)"],
                horizontal=True, label_visibility="collapsed")
is_full = "Full" in mode

st.markdown('<span class="slabel">GITHUB USERNAME</span>', unsafe_allow_html=True)

if is_full:
    username = st.text_input("u", placeholder="e.g. torvalds", label_visibility="collapsed")
else:
    c1, c2 = st.columns([4, 1])
    with c1:
        username = st.text_input("u", placeholder="e.g. torvalds", label_visibility="collapsed", key="qu")
    with c2:
        if st.button("Fetch", use_container_width=True):
            if username:
                with st.spinner("Fetching…"):
                    try:
                        r = fetch_github_repos(username)
                        st.session_state.fetched_repos = r["own_repos"] + r["oss_repos"]
                        st.session_state.github_username = username
                    except Exception as e:
                        handle_error(e)
            else:
                st.warning("Enter a username first.")

if not is_full and st.session_state.get("fetched_repos"):
    st.markdown('<span class="slabel">SELECT REPOSITORIES</span>', unsafe_allow_html=True)
    selected_repos = []
    with st.container(height=200):
        for repo in st.session_state.fetched_repos:
            desc  = (repo.get("description") or "")[:70]
            if st.checkbox(f"**{repo['name']}** — {desc}", key=f"r_{repo['name']}"):
                selected_repos.append(repo)
else:
    selected_repos = []

st.markdown('<span class="slabel">JOB DESCRIPTION</span>', unsafe_allow_html=True)
jd_text = st.text_area("jd", placeholder="Paste JD here…", height=220, label_visibility="collapsed")

with st.expander("✏️ Custom Instructions (optional)"):
    instructions = st.text_area("inst", placeholder="e.g. Focus on backend work…", height=80, label_visibility="collapsed")

st.markdown("<br>", unsafe_allow_html=True)
if st.button("🚀 Run Full Pipeline" if is_full else "🚀 Generate Resume", use_container_width=True):
    if not api_key:
        st.error("Add your API key in the sidebar.")
    elif not jd_text.strip():
        st.warning("Paste a job description first.")
    elif is_full:
        if not username:
            st.warning("Enter a GitHub username.")
        else:
            with st.spinner("Fetching repos…"):
                try:
                    r = fetch_github_repos(username)
                    repos = r["own_repos"] + r["oss_repos"]
                    if repos:
                        run_pipeline(username, repos, jd_text, instructions)
                    else:
                        st.warning("No repositories found.")
                except Exception as e:
                    handle_error(e)
    else:
        if not selected_repos:
            st.warning("Select at least one repository.")
        else:
            run_pipeline(st.session_state.github_username, selected_repos, jd_text, instructions)

# ── Results ───────────────────────────────────────────────────────────────────
if "resume_data" not in st.session_state:
    st.stop()

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")
tab1, tab2, tab3, tab4, tab5 = st.tabs(["📄 Resume", "📜 LaTeX Source", "🎯 Skill Gap", "📂 Project Overview", "🔍 JD Analyser"])

# ── Resume Preview ────────────────────────────────────────────────────────────
with tab1:
    d = st.session_state.resume_data
    p = d.get("profile", {})
    name    = p.get("name") or p.get("username") or d.get("name", "Candidate")
    gh_url  = p.get("github_url") or f"https://github.com/{p.get('username','')}"
    summary = d.get("summary") or p.get("summary") or ""

    skills_html = ""
    for cat, items in d.get("skills_section", {}).items():
        if items:
            tags = "".join(f"<span style='background:#f0f4ff;color:#3730a3;border-radius:5px;padding:2px 9px;margin:2px;font-size:0.78rem;display:inline-block'>{s}</span>" for s in items)
            skills_html += f"<p style='margin:0 0 8px'><strong style='color:#475569;font-size:0.72rem;text-transform:uppercase;letter-spacing:.05em'>{cat}:</strong><br>{tags}</p>"

    proj_html = ""
    for proj in d.get("projects", []):
        pn = proj.get("name",""); pu = proj.get("url") or proj.get("html_url","")
        tech = ", ".join(proj.get("tech_stack",[])); liner = proj.get("one_liner","")
        buls = "".join(f"<li style='margin-bottom:5px'>{b}</li>" for b in proj.get("bullets",[]))
        lnk  = f" <a href='{pu}' style='color:#6d28d9;font-size:.78rem' target='_blank'>↗</a>" if pu else ""
        proj_html += (
            f"<div style='margin-bottom:20px;padding-bottom:20px;border-bottom:1px solid #e5e7eb'>"
            f"<strong style='font-size:1rem'>{pn}{lnk}</strong>"
            f"<div style='color:#7c3aed;font-size:.78rem;font-weight:600;margin:2px 0'>{tech}</div>"
            f"<div style='color:#6b7280;font-style:italic;font-size:.85rem;margin-bottom:6px'>{liner}</div>"
            f"<ul style='margin:0;padding-left:16px;color:#374151;font-size:.88rem'>{buls}</ul></div>"
        )

    sum_block = f"<p style='color:#374151;font-size:.9rem;line-height:1.7;margin-bottom:24px'>{summary}</p>" if summary else ""

    html = (
        "<div style='background:white;color:#111;padding:44px;border-radius:10px;"
        "font-family:Inter,sans-serif;box-shadow:0 4px 20px rgba(0,0,0,.08);max-width:720px;margin:0 auto'>"
        f"<h1 style='margin:0 0 4px;font-size:1.9rem;font-weight:800'>{name}</h1>"
        f"<a href='{gh_url}' style='color:#7c3aed;font-size:.83rem;text-decoration:none'>{gh_url}</a>"
        "<hr style='border:none;border-top:2px solid #7c3aed;margin:18px 0'>"
        + (f"<h3 style='font-size:.72rem;color:#7c3aed;text-transform:uppercase;letter-spacing:.08em;margin:0 0 8px'>Summary</h3>{sum_block}" if summary else "")
        + "<h3 style='font-size:.72rem;color:#7c3aed;text-transform:uppercase;letter-spacing:.08em;margin:0 0 10px'>Technical Skills</h3>"
        + f"<div style='margin-bottom:24px'>{skills_html}</div>"
        + "<h3 style='font-size:.72rem;color:#7c3aed;text-transform:uppercase;letter-spacing:.08em;margin:0 0 14px'>Projects</h3>"
        + proj_html + "</div>"
    )
    st.html(html)
    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button("⬇️ Download LaTeX (.tex)", st.session_state.latex_code, "resume.tex", "text/plain", type="primary")

# ── Skill Gap ────────────────────────────────────────────────────────────────
with tab3:
    match_results = st.session_state.get("match_results", [])
    jd_profile    = st.session_state.get("jd_profile", {})

    if not match_results:
        st.info("Run the pipeline to see the skill gap analysis.")
    else:
        # Aggregate all matched skills across every repo (deduplicated)
        all_matched: dict[str, int] = {}   # skill → count of repos that matched it
        for r in match_results:
            for s in r.get("matched_skills", []):
                k = s.lower()
                all_matched[k] = all_matched.get(k, 0) + 1

        # Build the full JD required skill set
        skill_keys = ["technical_skills", "tools_and_technologies",
                      "programming_languages", "domain_knowledge", "nice_to_have"]
        jd_all: list[str] = []
        for key in skill_keys:
            jd_all.extend(jd_profile.get(key, []))
        jd_lower_map = {s.lower(): s for s in jd_all}   # lowercase → original label

        # Missing = in JD but not matched in any repo
        missing_all = [orig for lower, orig in jd_lower_map.items() if lower not in all_matched]

        # Stats row
        total = len(jd_lower_map) or 1
        pct   = int(len(all_matched) / total * 100)
        m1, m2, m3 = st.columns(3)
        m1.metric("✅ Matched", len(all_matched))
        m2.metric("❌ Missing", len(missing_all))
        m3.metric("🎯 Coverage", f"{pct}%")

        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)

        with c1:
            st.markdown("### ✅ Matched Skills")
            if all_matched:
                pills = "".join(
                    f'<span class="pill-ok">✓ {jd_lower_map.get(k, k)}</span>'
                    for k in sorted(all_matched)
                )
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.markdown("_No matches found_")

        with c2:
            st.markdown("### ❌ Missing Skills")
            if missing_all:
                pills = "".join(
                    f'<span class="pill-no">✗ {s}</span>'
                    for s in sorted(missing_all)
                )
                st.markdown(pills, unsafe_allow_html=True)
            else:
                st.markdown("_No gaps detected_ 🎉")

# ── Project Overview ──────────────────────────────────────────────────────────
with tab4:
    match_results = st.session_state.get("match_results", [])
    if not match_results:
        st.info("Run the pipeline to see the project breakdown.")
    else:
        st.markdown("#### 📂 Per-Repository Breakdown")
        for i, r in enumerate(match_results):
            score = r.get("match_score", 0)
            with st.expander(f"#{i+1} {r['name']} — {score}% Match", expanded=(i == 0)):
                rc1, rc2 = st.columns(2)
                with rc1:
                    matched = r.get("matched_skills", [])
                    st.markdown("".join(f'<span class="pill-ok">{s}</span>' for s in matched) or "_none_", unsafe_allow_html=True)
                with rc2:
                    missing = r.get("missing_skills", [])
                    st.markdown("".join(f'<span class="pill-no">{s}</span>' for s in missing[:15]) or "_none_", unsafe_allow_html=True)
                for h in r.get("highlights", []):
                    st.markdown(f"- {h}")


# ── JD Analyser ───────────────────────────────────────────────────────────────
with tab5:
    jd = st.session_state.get("jd_profile")
    if not jd:
        st.info("Run the pipeline to see the JD breakdown.")
    else:
        tech  = jd.get("technical_skills", [])
        tools = jd.get("tools_and_technologies", [])
        langs = jd.get("programming_languages", [])
        m1, m2, m3 = st.columns(3)
        m1.metric("Technical Skills", len(tech))
        m2.metric("Tools & Tech", len(tools))
        m3.metric("Languages", len(langs))
        st.markdown("<br>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("#### 🧠 Technical Skills")
            for s in tech: st.markdown(f"- {s}")
            if langs:
                st.markdown("#### 🖥️ Languages")
                st.markdown("  ".join(f"`{l}`" for l in langs))
        with c2:
            st.markdown("#### 🛠️ Tools & Tech")
            for t in tools: st.markdown(f"- {t}")
            exp = jd.get("experience_level", "")
            if exp: st.markdown(f"#### 📌 Experience\n{exp}")

# ── LaTeX Source ──────────────────────────────────────────────────────────────
with tab2:
    st.code(st.session_state.latex_code, language="latex")
    st.download_button("⬇️ Download .tex", st.session_state.latex_code, "resume.tex", "text/plain")
