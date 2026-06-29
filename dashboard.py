import os
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import json
import base64
import html as html_lib
import os
from mcp import StdioServerParameters
from client import ResumeMCPClient
import latex
import math

st.set_page_config(
    page_title="alldone v2 — GitHub to Job‑Ready Resume",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# ── Session state init ──────────────────────────────────────────────────────
INITIAL_STATE = {
    "github_metadata": None,
    "raw_repos": [],
    "repository_profiles": [],
    "jd_profile": None,
    "match_results": None,
    "overall_skill_gap": None,
    "resume_content": None,
    "latex_code": None,
    "username": "",
    "analysis_mode": "Full Analysis (Scan all repositories)",
    "groq_api_key": "",
    "gemini_api_key": "",
    "github_token": "",
    "jd_text": ""
}

for k, v in INITIAL_STATE.items():
    if k not in st.session_state:
        st.session_state[k] = v

mcp = ResumeMCPClient()

# ── Helper HTML generators ─────────────────────────────────────────────────
def generate_badges(items, badge_class):
    if not items:
        return ""
    return "".join([f"<span class='{badge_class}'>{html_lib.escape(i)}</span>" for i in items])

def get_repo_meta(repo_name):
    for r in st.session_state.raw_repos:
        if r["metadata"]["name"] == repo_name:
            return r["metadata"]
    return {}

def get_repo_profile(repo_name):
    for rp in st.session_state.repository_profiles:
        if rp["name"] == repo_name:
            return rp
    return {}

# ── Sidebar settings ────────────────────────────────────────────────────────
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
    
    default_model_idx = 0
    if os.environ.get("GEMINI_API_KEY") and not os.environ.get("GROQ_API_KEY"):
        default_model_idx = 1
        
    model_choice = st.selectbox(
        "LLM Provider",
        ["Groq (Llama 3.3 70B)", "Google (Gemini 2.5 Flash)", "Hugging Face (Qwen 72B)"],
        index=default_model_idx, label_visibility="collapsed",
    )
    
    # Conditional API Key block based on LLM choice
    if "Groq" in model_choice:
        st.markdown("<span class='input-label'>Groq API Key</span>", unsafe_allow_html=True)
        groq_key = st.text_input(
            "Groq API Key",
            type="password",
            value=st.session_state.get("groq_api_key", ""),
            placeholder="Enter Groq API Key...",
            help="Provide your own Groq API key to override environment key.",
            label_visibility="collapsed"
        )
        if groq_key != st.session_state.get("groq_api_key", ""):
            st.session_state.groq_api_key = groq_key
            if groq_key:
                os.environ["GROQ_API_KEY"] = groq_key
            else:
                load_dotenv(override=True)
            st.rerun()
            
        # Display key status
        if st.session_state.get("groq_api_key"):
            st.markdown("<span style='color: #4CAF50; font-size: 0.8rem;'>✍️ Using manually entered API Key</span>", unsafe_allow_html=True)
        elif os.environ.get("GROQ_API_KEY"):
            st.markdown("<span style='color: #8B949E; font-size: 0.8rem;'>🔑 Using API Key from environment (.env)</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: #FF9800; font-size: 0.8rem;'>⚠️ No API Key detected. Please enter one.</span>", unsafe_allow_html=True)
            
        st.markdown("<small><a href='https://console.groq.com/keys' target='_blank'>Get free Groq API Key</a></small>", unsafe_allow_html=True)
    elif "Hugging" in model_choice:
        st.markdown("<span class='input-label'>Hugging Face Token</span>", unsafe_allow_html=True)
        hf_token = st.text_input(
            "HF Token",
            type="password",
            value=st.session_state.get("hf_token", ""),
            placeholder="Enter HF Token...",
            help="Provide your own Hugging Face token to use the Inference API.",
            label_visibility="collapsed"
        )
        if hf_token != st.session_state.get("hf_token", ""):
            st.session_state.hf_token = hf_token
            if hf_token:
                os.environ["HF_TOKEN"] = hf_token
            else:
                load_dotenv(override=True)
            st.rerun()
            
        # Display key status
        if st.session_state.get("hf_token"):
            st.markdown("<span style='color: #4CAF50; font-size: 0.8rem;'>✍️ Using manually entered HF Token</span>", unsafe_allow_html=True)
        elif os.environ.get("HF_TOKEN"):
            st.markdown("<span style='color: #8B949E; font-size: 0.8rem;'>🔑 Using HF Token from environment (.env)</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: #FF9800; font-size: 0.8rem;'>⚠️ No HF Token detected. Required for this provider.</span>", unsafe_allow_html=True)
            
        st.markdown("<small><a href='https://huggingface.co/settings/tokens' target='_blank'>Get free HF Token</a></small>", unsafe_allow_html=True)
    else:
        st.markdown("<span class='input-label'>Gemini API Key</span>", unsafe_allow_html=True)
        gemini_key = st.text_input(
            "Gemini API Key",
            type="password",
            value=st.session_state.get("gemini_api_key", ""),
            placeholder="Enter Gemini API Key...",
            help="Provide your own Gemini API key to override environment key.",
            label_visibility="collapsed"
        )
        if gemini_key != st.session_state.get("gemini_api_key", ""):
            st.session_state.gemini_api_key = gemini_key
            if gemini_key:
                os.environ["GEMINI_API_KEY"] = gemini_key
            else:
                load_dotenv(override=True)
            st.rerun()
            
        # Display key status
        if st.session_state.get("gemini_api_key"):
            st.markdown("<span style='color: #4CAF50; font-size: 0.8rem;'>✍️ Using manually entered API Key</span>", unsafe_allow_html=True)
        elif os.environ.get("GEMINI_API_KEY"):
            st.markdown("<span style='color: #8B949E; font-size: 0.8rem;'>🔑 Using API Key from environment (.env)</span>", unsafe_allow_html=True)
        else:
            st.markdown("<span style='color: #FF9800; font-size: 0.8rem;'>⚠️ No API Key detected. Please enter one.</span>", unsafe_allow_html=True)
            
        st.markdown("<small><a href='https://aistudio.google.com/app/apikey' target='_blank'>Get free Gemini API Key</a></small>", unsafe_allow_html=True)

    # Separate GitHub Token block
    st.markdown("<span class='input-label'>GitHub Token (Optional)</span>", unsafe_allow_html=True)
    gh_token = st.text_input(
        "GitHub Token",
        type="password",
        value=st.session_state.get("github_token", ""),
        placeholder="Enter GitHub Token...",
        help="Only required if GITHUB_TOKEN is not already available in environment variables.",
        label_visibility="collapsed"
    )
    if gh_token != st.session_state.get("github_token", ""):
        st.session_state.github_token = gh_token
        if gh_token:
            os.environ["GITHUB_TOKEN"] = gh_token
        else:
            load_dotenv(override=True)
        st.rerun()
        
    # Display token status
    if st.session_state.get("github_token"):
        st.markdown("<span style='color: #4CAF50; font-size: 0.8rem;'>✍️ Using manually entered Token</span>", unsafe_allow_html=True)
    elif os.environ.get("GITHUB_TOKEN"):
        st.markdown("<span style='color: #8B949E; font-size: 0.8rem;'>🔑 Using Token from environment (.env)</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='color: #8B949E; font-size: 0.8rem;'>ℹ️ No GitHub Token detected (Rate limits may apply).</span>", unsafe_allow_html=True)
        
    st.markdown("<small><a href='https://github.com/settings/tokens' target='_blank'>Create GitHub Personal Access Token</a></small>", unsafe_allow_html=True)

    
    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    max_projects = st.slider("Default Projects in Resume", min_value=1, max_value=6, value=3)

    st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
    if st.button("🔄 Reset All", use_container_width=True):
        st.session_state.clear()
        for k, v in INITIAL_STATE.items():
            st.session_state[k] = v
        st.rerun()

def handle_error(e):
    import traceback
    error_msg = str(e)
    error_msg_lower = error_msg.lower()
    
    if "tokens per day" in error_msg_lower or "tpd" in error_msg_lower:
        import re
        time_match = re.search(r"Please try again in ([0-9a-z\.]+)", error_msg)
        time_left = time_match.group(1) if time_match else "24 hours"
        st.error(f"🚨 **Groq Daily Token Limit Exhausted!**\n\nYour account has reached its daily limit because Full Analysis scans massive amounts of code.\n\n**How to fix:**\n1. Wait until your quota resets in **{time_left}**.\n2. Create a new Groq API key using a **different Google/GitHub account** and paste it in the Custom API Keys sidebar.\n3. **Switch the LLM Provider to Google Gemini**, which has a much larger free tier!")
        
    elif "quota exceeded" in error_msg_lower or "resourceexhausted" in error_msg_lower or "429" in error_msg_lower and "groq" not in error_msg_lower and "huggingface" not in error_msg_lower:
        import re
        time_match = re.search(r"retry in ([0-9a-zA-Z\.\s]+)", error_msg)
        if not time_match:
            time_match = re.search(r"seconds:\s*(\d+)", error_msg)
        time_left = time_match.group(1) if time_match else "30 seconds"
        st.error(f"🚨 **Gemini API Rate Limit/Quota Exceeded!**\n\nGoogle Gemini's free tier has a strict limit of 15/20 requests per minute.\n\n**How to fix:**\n1. Wait **{time_left}** for the current window to reset, then click retry.\n2. **Switch to Quick Analysis mode** to only scan 2 or 3 select repositories (uses significantly fewer API calls).\n3. **Switch to Groq (Llama 3.3)** by providing a Groq API key in the sidebar.")
        
    elif "huggingface" in error_msg_lower or "hf_token" in error_msg_lower or "hugging face" in error_msg_lower:
        st.error(f"🚨 **Hugging Face Rate Limit Exhausted!**\n\nYou have hit the anonymous rate limit.\n\n**How to fix:**\n1. **Add an HF Token** in the sidebar settings to get a much larger quota.\n2. **Switch to Google Gemini**, which has a large free tier.")
        
    else:
        st.error(f"🚨 **Application Error**\n\nAn unexpected error occurred during execution:\n\n**Details**: `{error_msg}`\n\n```python\n{traceback.format_exc()}\n```")

# ── Header / Analysis Inputs ─────────────────────────────────────
show_results = st.session_state.match_results is not None

with st.expander("🔍 Configure & Run Analysis", expanded=True):
    st.markdown("<span class='input-label'>Analysis Mode</span>", unsafe_allow_html=True)
    analysis_mode = st.radio(
        "Analysis Mode",
        options=["Full Analysis (Scan all repositories)", "Quick Analysis (Select Repositories)"],
        label_visibility="collapsed",
        horizontal=True,
    )
    st.session_state.analysis_mode = analysis_mode

    if "Full Analysis" in st.session_state.analysis_mode:
        username = st.text_input("GitHub Username", value=st.session_state.username, placeholder="e.g. torvalds", key="full_user_input")
        if username != st.session_state.username:
            st.session_state.username = username
            
        jd_text = st.text_area("Job Description", value=st.session_state.get("jd_text", ""), height=150, placeholder="Paste JD here...", key="full_jd_input")
        if jd_text != st.session_state.get("jd_text", ""):
            st.session_state.jd_text = jd_text
    
        if st.button("🚀 Run Full Pipeline"):
            missing_key = ("Groq" in model_choice and not st.session_state.get("groq_api_key") and not os.environ.get("GROQ_API_KEY")) or \
                          ("Gemini" in model_choice and not st.session_state.get("gemini_api_key") and not os.environ.get("GEMINI_API_KEY"))
            
            if missing_key:
                st.warning(f"⚠️ Please enter your {model_choice.split()[0]} API Key in the settings sidebar.")
            elif not username or not jd_text:
                st.warning("⚠️ Please provide both a GitHub username and a Job Description.")
            else:
                st.session_state.username = username
                try:
                    st.session_state.match_results = None
                    st.session_state.overall_skill_gap = None
                    st.session_state.resume_content = None
                    st.session_state.latex_code = None
                    with st.status("Running Full Analysis...", expanded=True) as status:
                        pbar = st.progress(0, text=f"Step 1/6: Extracting GitHub Profile & Metadata with {model_choice}...")
                        res = mcp.call("extract_github_metadata", {
                            "username": username, 
                            "model_choice": model_choice
                        })
                        st.session_state.github_metadata = res["dashboard"]
                        st.session_state.raw_repos = res["raw_repos"]
                        
                        repos_to_scan = [r["metadata"]["name"] for r in st.session_state.raw_repos]
                        pbar.progress(15, text=f"Step 2/6: Extracting knowledge for {len(repos_to_scan)} repositories (using caching)...")
                        build_res = mcp.call("build_repository_profiles", {
                            "username": username,
                            "raw_repos": st.session_state.raw_repos,
                            "selected_repo_names": repos_to_scan,
                            "model_choice": model_choice
                        })
                        if isinstance(build_res, dict):
                            profiles = build_res["profiles"]
                            st.session_state.raw_repos = build_res["raw_repos"]
                        else:
                            profiles = build_res
                        st.session_state.repository_profiles = profiles
                        
                        pbar.progress(40, text=f"Step 3/6: Structuring Job Description requirements...")
                        jd_prof = mcp.call("analyze_jd", {"jd_text": jd_text, "model_choice": model_choice})
                        st.session_state.jd_profile = jd_prof
                        
                        pbar.progress(55, text=f"Step 4/6: Matching & Scoring {len(profiles)} Repositories...")
                        match_res = mcp.call("match_repositories", {
                            "repo_profiles": profiles,
                            "jd_profile": jd_prof,
                            "raw_repos": st.session_state.raw_repos,
                            "model_choice": model_choice
                        })
                        
                        st.session_state.match_results = match_res["ranked_matches"]
                        st.session_state.overall_skill_gap = match_res["overall_skill_gap"]
                        
                        pbar.progress(70, text=f"Step 5/6: Extracting OSS Contributions...")
                        auto_selected_repos = [m['repository_name'] for m in st.session_state.match_results[:max_projects]]
                        st.session_state.selected_for_resume = auto_selected_repos
                        
                        oss_contribs = mcp.call("extract_oss", {"username": st.session_state.username, "model_choice": model_choice})
                        selected_profiles = [rp for rp in st.session_state.repository_profiles if rp['name'] in auto_selected_repos]
                        
                        pbar.progress(85, text=f"Step 6/6: Generating AI Resume and LaTeX Code...")
                        resume = mcp.call("generate_resume", {
                            "profile_dict": st.session_state.github_metadata["profile"],
                            "selected_repo_profiles": selected_profiles,
                            "jd_profile_dict": st.session_state.jd_profile,
                            "match_results": st.session_state.match_results,
                            "user_instructions": "Highlight the most relevant technical achievements.",
                            "model_choice": model_choice,
                            "oss_contributions": oss_contribs
                        })
                        resume["pages"] = pages
                        st.session_state.resume_content = resume
                        st.session_state.latex_code = latex.generate_latex(resume, "ATS Classic")
                        
                        pbar.progress(100, text="Pipeline Complete!")
                        status.update(label="✅ Full Pipeline Complete!", state="complete")
                    st.rerun()
                except Exception as e:
                    handle_error(e)
    
    else:
        # Quick Analysis Flow
        st.markdown("<span class='input-label'>GitHub Username</span>", unsafe_allow_html=True)
        username = st.text_input("GitHub Username", value=st.session_state.username, placeholder="e.g. torvalds", key="quick_user", label_visibility="collapsed")
        if username != st.session_state.username:
            st.session_state.username = username
        
        if st.button("Fetch GitHub Metadata"):
            missing_key = ("Groq" in model_choice and not st.session_state.get("groq_api_key") and not os.environ.get("GROQ_API_KEY")) or \
                          ("Gemini" in model_choice and not st.session_state.get("gemini_api_key") and not os.environ.get("GEMINI_API_KEY"))
            
            if missing_key:
                st.warning(f"⚠️ Please enter your {model_choice.split()[0]} API Key in the settings sidebar.")
            elif username:
                try:
                    with st.spinner("Extracting Profile & Repository Metadata..."):
                        res = mcp.call("extract_github_metadata", {
                            "username": username, 
                            "model_choice": model_choice
                        })
                        if not res.get("raw_repos"):
                            st.warning(f"No public repositories found for GitHub user '{username}'. Please check the username spelling.")
                            st.session_state.github_metadata = None
                            st.session_state.raw_repos = []
                        else:
                            st.session_state.github_metadata = res["dashboard"]
                            st.session_state.raw_repos = res["raw_repos"]
                            st.session_state.username = username
                        st.rerun()
                except Exception as e:
                    handle_error(e)
    
        if st.session_state.github_metadata and not st.session_state.repository_profiles:
            st.markdown("<br><span class='input-label'>Select Repositories for Analysis</span>", unsafe_allow_html=True)
            if "quick_selected_repos" not in st.session_state:
                st.session_state.quick_selected_repos = [r["metadata"]["name"] for r in st.session_state.raw_repos[:max_projects]]

            selected_repos = []
            for r in st.session_state.raw_repos:
                repo_name = r["metadata"]["name"]
                repo_url = r["metadata"]["url"]
                repo_desc = r["metadata"].get("description") or "No description provided."
                
                col1, col2 = st.columns([0.05, 0.95])
                with col1:
                    is_sel = st.checkbox("Select Repo", key=f"quick_sel_{repo_name}", value=(repo_name in st.session_state.quick_selected_repos), label_visibility="collapsed")
                    if is_sel:
                        selected_repos.append(repo_name)
                with col2:
                    st.markdown(f"**[{repo_name}]({repo_url})**<br><span style='color:#8B949E; font-size:0.9rem;'>{html_lib.escape(repo_desc)}</span>", unsafe_allow_html=True)
            
            st.session_state.quick_selected_repos = selected_repos
            
            st.markdown("<br><span class='input-label'>Job Description Matching</span>", unsafe_allow_html=True)
            jd_text = st.text_area("Paste Job Description", value=st.session_state.get("jd_text", ""), height=150, label_visibility="collapsed", key="quick_jd_input")
            if jd_text != st.session_state.get("jd_text", ""):
                st.session_state.jd_text = jd_text
            
            if st.button("Run Pipeline on Selected Repos", type="primary"):
                missing_key = ("Groq" in model_choice and not st.session_state.get("groq_api_key") and not os.environ.get("GROQ_API_KEY")) or \
                              ("Gemini" in model_choice and not st.session_state.get("gemini_api_key") and not os.environ.get("GEMINI_API_KEY"))
                
                if missing_key:
                    st.warning(f"⚠️ Please enter your {model_choice.split()[0]} API Key in the settings sidebar.")
                elif not jd_text:
                    st.warning("⚠️ Please provide a Job Description.")
                elif not selected_repos:
                    st.warning("⚠️ Please select at least one repository.")
                else:
                    try:
                        st.session_state.match_results = None
                        st.session_state.overall_skill_gap = None
                        st.session_state.resume_content = None
                        st.session_state.latex_code = None
                        with st.status("Running Quick Analysis...", expanded=True) as status:
                            pbar = st.progress(0, text=f"Step 1/5: Extracting knowledge for {len(selected_repos)} repositories (using caching)...")
                            build_res = mcp.call("build_repository_profiles", {
                                "username": st.session_state.username,
                                "raw_repos": st.session_state.raw_repos,
                                "selected_repo_names": selected_repos,
                                "model_choice": model_choice
                            })
                            if isinstance(build_res, dict):
                                profiles = build_res["profiles"]
                                st.session_state.raw_repos = build_res["raw_repos"]
                            else:
                                profiles = build_res
                            st.session_state.repository_profiles = profiles
                            
                            pbar.progress(25, text=f"Step 2/5: Structuring Job Description requirements...")
                            jd_prof = mcp.call("analyze_jd", {"jd_text": jd_text, "model_choice": model_choice})
                            st.session_state.jd_profile = jd_prof
                            
                            pbar.progress(45, text=f"Step 3/5: Matching & Scoring Repositories...")
                            match_res = mcp.call("match_repositories", {
                                "repo_profiles": profiles,
                                "jd_profile": jd_prof,
                                "raw_repos": st.session_state.raw_repos,
                                "model_choice": model_choice
                            })
                            
                            st.session_state.match_results = match_res["ranked_matches"]
                            st.session_state.overall_skill_gap = match_res["overall_skill_gap"]
                            
                            pbar.progress(65, text=f"Step 4/5: Extracting OSS Contributions...")
                            auto_selected_repos = [m['repository_name'] for m in st.session_state.match_results[:max_projects]]
                            st.session_state.selected_for_resume = auto_selected_repos
                            
                            oss_contribs = mcp.call("extract_oss", {"username": st.session_state.username, "model_choice": model_choice})
                            selected_profiles = [rp for rp in st.session_state.repository_profiles if rp['name'] in auto_selected_repos]
                            
                            pbar.progress(85, text=f"Step 5/5: Generating AI Resume and LaTeX Code...")
                            resume = mcp.call("generate_resume", {
                                "profile_dict": st.session_state.github_metadata["profile"],
                                "selected_repo_profiles": selected_profiles,
                                "jd_profile_dict": st.session_state.jd_profile,
                                "match_results": st.session_state.match_results,
                                "user_instructions": "Highlight the most relevant technical achievements.",
                                "model_choice": model_choice,
                                "oss_contributions": oss_contribs
                            })
                            resume["pages"] = pages
                            st.session_state.resume_content = resume
                            st.session_state.latex_code = latex.generate_latex(resume, "ATS Classic")
                            
                            pbar.progress(100, text="Pipeline Complete!")
                            status.update(label="✅ Quick Analysis & Resume Generation Complete!", state="complete")
                        st.rerun()
                    except Exception as e:
                        handle_error(e)

# --- Full Application View ---
if st.session_state.match_results:
    col1, col2 = st.columns([0.85, 0.15])
    with col2:
        if st.button("🔄 Reset Analysis", use_container_width=True, type="secondary"):
            st.session_state.clear()
            for k, v in INITIAL_STATE.items():
                st.session_state[k] = v
            st.rerun()

    tab1, tab2, tab3, tab4 = st.tabs([
        "📄 Resume", "📂 Projects", "🎯 Skill Gap", "📋 Job Description"
    ])

    # --- 1. RESUME TAB ---
    with tab1:
        if "selected_for_resume" not in st.session_state:
            st.session_state.selected_for_resume = [m['repository_name'] for m in st.session_state.match_results[:max_projects]]

        with st.expander("🛠️ Custom Instructions & Regeneration", expanded=False):
            instructions = st.text_area("Custom Instructions (Optional)", placeholder="e.g. Focus on backend...", key="res_instructions")
            include_oss = st.checkbox("Include Open Source Contributions", value=True, key="res_include_oss")
            if st.button("Regenerate Resume", type="primary", key="res_regenerate_btn"):
                with st.spinner("Regenerating Resume..."):
                    selected_repos = st.session_state.selected_for_resume
                    selected_profiles = [rp for rp in st.session_state.repository_profiles if rp['name'] in selected_repos]
                    
                    oss_contribs = []
                    if include_oss:
                        oss_contribs = mcp.call("extract_oss", {"username": st.session_state.username, "model_choice": model_choice})
                        
                    resume = mcp.call("generate_resume", {
                        "profile_dict": st.session_state.github_metadata["profile"],
                        "selected_repo_profiles": selected_profiles,
                        "jd_profile_dict": st.session_state.jd_profile,
                        "match_results": st.session_state.match_results,
                        "user_instructions": instructions,
                        "model_choice": model_choice,
                        "oss_contributions": oss_contribs
                    })
                    resume["pages"] = pages
                    st.session_state.resume_content = resume
                    st.session_state.latex_code = latex.generate_latex(resume, "ATS Classic")
                st.rerun()

        if st.session_state.resume_content:
            data = st.session_state.resume_content
            
            # Construct HTML
            html = "<div class='resume-preview'>"
            html += f"<div class='resume-name'>{data['profile']['name']}</div>"
            
            contact_items = []
            if data['profile'].get('email'): contact_items.append(data['profile']['email'])
            if data['profile'].get('github_url'): contact_items.append(data['profile']['github_url'])
            if data['profile'].get('linkedin_url'): contact_items.append(data['profile']['linkedin_url'])
            if data['profile'].get('website') and data['profile'].get('website') not in contact_items: contact_items.append(data['profile']['website'])
            
            html += f"<div class='resume-contact'>{' • '.join(contact_items)}</div>"
            html += f"<div class='resume-section-title'>Summary</div><div style='margin-bottom:8px'>{data.get('summary', '')}</div>"
            
            if data.get("skills_section"):
                html += "<div class='resume-section-title'>Technical Skills</div>"
                skills_items = []
                for cat, items in data["skills_section"].items():
                    if items:
                        skills_items.append(f"<div style='margin-bottom:4px;'><b>{html_lib.escape(cat)}:</b> {html_lib.escape(', '.join(items))}</div>")
                html += "".join(skills_items)
                html += "<div style='margin-bottom:10px;'></div>"
            
            html += "<div class='resume-section-title'>Projects</div>"
            for proj in data.get("projects", []):
                tech_stack = ", ".join(proj.get("tech_stack", []))
                tech_str = f" | <i>{tech_stack}</i>" if tech_stack else ""
                html += f"<div style='font-weight:bold;'>{proj['name']}{tech_str}</div>"
                html += f"<div style='font-style:italic; margin-bottom: 4px; font-size: 0.9em;'>{proj['one_liner']}</div>"
                for bullet in proj.get("bullets", []):
                    html += f"<div style='margin-left:12px'>• {bullet}</div>"
            
            if data.get("contributions"):
                html += "<div class='resume-section-title'>Open Source Contributions</div>"
                for oss in data["contributions"]:
                    tech_stack = ", ".join(oss.get("tech_stack", []))
                    tech_str = f" | <i>{tech_stack}</i>" if tech_stack else ""
                    html += f"<div style='font-weight:bold;'>{oss.get('name', 'Repository')}{tech_str}</div>"
                    html += f"<div style='font-style:italic; margin-bottom:2px; font-size: 0.9em;'>{oss.get('desc', '')}</div>"
                    
            html += "</div>"
            
            # Toggle between Resume Preview and LaTeX Source
            view_mode = st.radio(
                "Select View Mode",
                ["📄 Resume Preview", "📜 LaTeX Source"],
                horizontal=True,
                label_visibility="collapsed",
                key="resume_view_mode"
            )
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if "Resume Preview" in view_mode:
                st.markdown("## 📄 Resume Preview")
                st.markdown(html, unsafe_allow_html=True)
            else:
                st.markdown("## 📜 LaTeX Source Code")
                if st.session_state.latex_code:
                    st.code(st.session_state.latex_code, language="latex")
                    st.download_button(
                        label="⬇️ Download .tex",
                        data=st.session_state.latex_code,
                        file_name="resume.tex",
                        mime="text/plain",
                        use_container_width=True,
                        key="res_download_tex"
                    )

    # --- 2. PROJECTS TAB ---
    with tab2:
        total_analysed = len(st.session_state.match_results)
        top_match = max([m['overall_score'] for m in st.session_state.match_results]) * 100 if total_analysed else 0
        avg_match = sum([m['overall_score'] for m in st.session_state.match_results]) / total_analysed * 100 if total_analysed else 0
        gap = st.session_state.overall_skill_gap
        
        st.markdown(f"""
        <div class='metrics-bar'>
            <div class='metric-card'>
                <div class='metric-value'>{total_analysed}</div>
                <div class='metric-label'>Projects Analysed</div>
            </div>
            <div class='metric-card'>
                <div class='metric-value'>{top_match:.0f}%</div>
                <div class='metric-label'>Top Match</div>
            </div>
            <div class='metric-card'>
                <div class='metric-value'>{avg_match:.0f}%</div>
                <div class='metric-label'>Avg Match</div>
            </div>
            <div class='metric-card'>
                <div class='metric-value'>{len(gap['missing_skills'])}</div>
                <div class='metric-label'>Skill Gaps</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        
        display_results = st.session_state.match_results.copy()
        display_results = sorted(display_results, key=lambda x: x['overall_score'], reverse=True)
            
        for idx, mr in enumerate(display_results):
            repo_name = mr['repository_name']
            meta = get_repo_meta(repo_name)
            prof = get_repo_profile(repo_name)
            jd = st.session_state.jd_profile
            
            score = int(mr['overall_score'] * 100)
            stars = meta.get('stars', 0)
            desc = prof.get('one_line_summary', '')
            
            # Calculate accurate sub-scores based on LLM extraction
            total_skills = len(mr.get('matched_skills', [])) + len(mr.get('missing_skills', []))
            skill_match = min(100, int(len(mr.get('matched_skills', [])) / max(1, total_skills) * 100))
            
            jd_tech = jd.get('tools', []) + jd.get('frameworks', []) + jd.get('libraries', [])
            repo_tech = mr.get('matched_libraries', []) + mr.get('matched_frameworks', []) + mr.get('matched_tools', [])
            if jd_tech:
                tech_match = min(100, int(len(repo_tech) / len(jd_tech) * 100))
            else:
                tech_match = 100
                
            domain_str = mr.get('matched_domain', '')
            domain_match = 100 if prof.get('domain', '').lower() in jd.get('domain', '').lower() or domain_str else 50
            
            if jd.get('keywords'):
                keyword_match = min(100, int(len(mr.get('matched_keywords', [])) / max(1, len(jd.get('keywords', []))) * 100))
            else:
                keyword_match = 100
            
            matched_set = {x.lower() for x in mr.get('matched_skills', [])}
            skills_html = ""
            for s in prof.get('primary_skills', [])[:6]:
                if s.lower() in matched_set:
                    skills_html += f"<span class='badge-matched' style='margin: 0 2px 2px 0; padding: 2px 6px; font-size: 0.75rem; display: inline-block;'>{html_lib.escape(s)}</span>"
                else:
                    skills_html += f"<span class='tag'>{html_lib.escape(s)}</span>"
            
            card_html = f"""
            <div class='proj-card'>
                <div class='proj-rank'>#{idx+1}</div>
                <div class='proj-header'>
                    <strong style='font-size:1.3rem; color:#E6EDF3;'>{html_lib.escape(repo_name)}</strong>
                    <div>
                        <span class='proj-stars'>⭐ {stars}</span>
                        <span class='proj-match'>⚡ {score}% Match</span>
                    </div>
                </div>
                <div style='color:#8B949E; margin-bottom:10px;'>{html_lib.escape(desc)}</div>
                <div>{skills_html}</div>
            </div>
            """
            st.markdown(card_html, unsafe_allow_html=True)
            
            with st.expander("▼ View Detailed Analysis"):
                st.markdown(f"""
                <div class='score-row'>
                    <div class='score-card'>
                        <div class='score-num cyan'>{domain_match}%</div>
                        <div class='score-sub'>Domain Match</div>
                    </div>
                    <div class='score-card'>
                        <div class='score-num green'>{skill_match}%</div>
                        <div class='score-sub'>Skill Match</div>
                    </div>
                    <div class='score-card'>
                        <div class='score-num'>{tech_match}%</div>
                        <div class='score-sub'>Technology Match</div>
                    </div>
                    <div class='score-card'>
                        <div class='score-num'>{keyword_match}%</div>
                        <div class='score-sub'>Keyword Match</div>
                    </div>
                    <div class='score-card'>
                        <div class='score-num purple'>{score}%</div>
                        <div class='score-sub'>Overall Match</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("**Matched Skills**")
                    st.markdown(generate_badges(mr['matched_skills'], "badge-matched"), unsafe_allow_html=True)
                with c2:
                    st.markdown("**Missing Skills**")
                    st.markdown(generate_badges(mr['missing_skills'], "badge-missing"), unsafe_allow_html=True)
                    
                st.markdown("---")
                st.markdown("**Match Reason & Evidence**")
                if mr.get('evidence'):
                    for k, v in mr['evidence'].items():
                        st.markdown(f"✅ **{k}**: {v}")

    # --- 3. SKILL GAP TAB ---
    with tab3:
        gap = st.session_state.overall_skill_gap
        
        st.markdown("### Overall Matched Skills")
        st.markdown(generate_badges(gap['matched_skills'], "badge-matched"), unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown("### Overall Missing Skills")
        missing_names = [m['skill'] if isinstance(m, dict) else m for m in gap['missing_skills']]
        st.markdown(generate_badges(missing_names, "badge-missing"), unsafe_allow_html=True)
        
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown("### Recommended Learning")
        
        for m in gap['missing_skills']:
            skill_name = m['skill'] if isinstance(m, dict) else m
            rec = m.get('recommendation', f"Add {skill_name} to a project") if isinstance(m, dict) else f"Add {skill_name} to a project"
            
            st.markdown(f"""
            <div class='learn-row'>
                <div class='learn-skill'>{html_lib.escape(skill_name)}</div>
                <div class='learn-arrow'>→</div>
                <div class='learn-tip'>{html_lib.escape(rec)}</div>
            </div>
            """, unsafe_allow_html=True)

    # --- 4. JOB DESCRIPTION TAB ---
    with tab4:
        jd = st.session_state.jd_profile
        if not isinstance(jd, dict):
            # Sometimes JD is stored as a pydantic model in session state depending on where it came from
            if hasattr(jd, 'model_dump'):
                jd = jd.model_dump()
            elif hasattr(jd, 'dict'):
                jd = jd.dict()
                
        st.markdown("### Job Description Analysis")
        st.markdown(f"**Role:** {html_lib.escape(jd.get('role', jd.get('position', 'N/A')))}")
        st.markdown(f"**Domain:** {html_lib.escape(jd.get('domain', 'N/A'))}")
        st.markdown(f"**Experience Level:** {html_lib.escape(jd.get('experience_level', 'N/A'))}")
        
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        st.markdown("**Responsibilities**")
        for res in jd.get('responsibilities', []):
            st.markdown(f"- {html_lib.escape(res)}")
            
        st.markdown("<div class='section-divider'></div>", unsafe_allow_html=True)
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Required Skills**")
            st.markdown(generate_badges(jd.get('required_skills', []), "badge-missing"), unsafe_allow_html=True)
        with c2:
            st.markdown("**Preferred Skills**")
            st.markdown(generate_badges(jd.get('preferred_skills', []), "tag"), unsafe_allow_html=True)
            
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**Programming Languages:** {', '.join(jd.get('programming_languages', []))}")
        st.markdown(f"**Frameworks:** {', '.join(jd.get('frameworks', []))}")
        st.markdown(f"**Libraries:** {', '.join(jd.get('libraries', []))}")
        st.markdown(f"**Cloud & Databases:** {', '.join(jd.get('cloud', []) + jd.get('databases', []))}")
        st.markdown(f"**DevOps & Tools:** {', '.join(jd.get('devops', []) + jd.get('tools', []))}")
        st.markdown(f"**ATS Keywords:** {', '.join(jd.get('ats_keywords', []) + jd.get('keywords', []))}")