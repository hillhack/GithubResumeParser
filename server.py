import base64
import json
import logging
import os
import time
from typing import Any, Dict, List
import requests
from dotenv import load_dotenv
from groq import Groq
from mcp.server.fastmcp import FastMCP

load_dotenv()
logging.basicConfig(level=logging.INFO, stream=os.sys.stderr)
log = logging.getLogger(__name__)

mcp = FastMCP("alldone")

GITHUB_API = "https://api.github.com"
_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
AUTH = (_CLIENT_ID, _CLIENT_SECRET) if _CLIENT_ID else None

def get_llm_response(sys_prompt: str, user_prompt: str, model_choice: str, temperature: float = 0.1) -> str:
    """Dispatches request to appropriate LLM API. Retries on 429 rate-limit errors."""
    max_retries = 3
    base_wait = 15  # seconds — shorter than Groq's suggested retry-after for most limits

    if "Groq" in model_choice:
        from groq import Groq
        import groq as groq_module
        client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        for attempt in range(max_retries):
            try:
                resp = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
                    temperature=temperature, response_format={"type": "json_object"}
                )
                return resp.choices[0].message.content or "{}"
            except groq_module.RateLimitError as e:
                err_str = str(e)
                # TPD = daily token budget exhausted — retrying is useless, raise immediately
                is_daily_limit = ("tokens per day" in err_str or "TPD" in err_str or "per_day" in err_str)
                if is_daily_limit:
                    log.error(f"Groq DAILY token limit exhausted. Will use keyword fallback. {e}")
                    raise  # no point retrying
                # RPM = per-minute limit — exponential backoff is appropriate
                if attempt < max_retries - 1:
                    wait = base_wait * (2 ** attempt)  # 15s, 30s, 60s
                    log.warning(f"Groq 429 rate limit — waiting {wait}s before retry {attempt+1}/{max_retries-1}")
                    time.sleep(wait)
                else:
                    log.error(f"Groq rate limit exhausted after {max_retries} attempts: {e}")
                    raise
    elif "Gemini" in model_choice:
        from google import genai
        from google.genai import types
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        response = client.models.generate_content(
            model='gemini-1.5-pro',
            contents=f"System Instruction: {sys_prompt}\n\nUser Request: {user_prompt}",
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=temperature,
            ),
        )
        return response.text or "{}"
    return "{}"

def _safe_get(url: str, params: dict | None = None) -> requests.Response:
    try:
        resp = requests.get(url, auth=AUTH, timeout=15, params=params or {})
        resp.raise_for_status()
        return resp
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            log.debug(f"HTTP 404 Not Found: {url}")
        else:
            log.error(f"HTTP error {url}: {e}")
        raise
    except Exception as e:
        log.error(f"HTTP error {url}: {e}")
        raise

# --- TOOLS ---

@mcp.tool()
def extract_github_profile(username: str) -> str:
    """Extracts GitHub profile, repos, languages, and READMEs for a given user. Returns JSON."""
    log.info(f"Extracting profile for {username}")
    profile_data = _safe_get(f"{GITHUB_API}/users/{username}").json()
    profile = {
        "username": profile_data.get("login", username),
        "name": profile_data.get("name") or username,
        "bio": profile_data.get("bio") or "",
        "location": profile_data.get("location") or "",
        "email": profile_data.get("email") or "",
        "blog": profile_data.get("blog") or "",
        "public_repos": profile_data.get("public_repos", 0),
        "followers": profile_data.get("followers", 0),
        "avatar_url": profile_data.get("avatar_url", ""),
        "html_url": profile_data.get("html_url", ""),
    }

    repos = []
    page = 1
    while len(repos) < 60:
        batch = _safe_get(f"{GITHUB_API}/users/{username}/repos", params={"per_page": 100, "sort": "updated", "page": page}).json()
        if not batch: break
        for r in batch:
            is_fork = r.get("fork", False)
            if is_fork:
                try:
                    commits = _safe_get(f"{GITHUB_API}/repos/{username}/{r['name']}/commits", params={"author": username, "per_page": 1}).json()
                    if not isinstance(commits, list) or len(commits) == 0:
                        continue
                except Exception:
                    continue

            repos.append({
                "name": r["name"],
                "description": r.get("description") or "",
                "html_url": r.get("html_url", ""),
                "topics": r.get("topics", []),
                "language": r.get("language") or "",
                "stargazers_count": r.get("stargazers_count", 0),
                "forks_count": r.get("forks_count", 0),
                "is_fork": is_fork,
            })
        page += 1
        if len(batch) < 100: break
        
    repos.sort(key=lambda r: r["stargazers_count"], reverse=True)
    repos = repos[:60]

    # Enrich top 20
    for repo in repos[:20]:
        try:
            readme_data = _safe_get(f"{GITHUB_API}/repos/{username}/{repo['name']}/readme").json()
            content = readme_data.get("content", "")
            repo["readme"] = base64.b64decode(content).decode("utf-8", errors="replace")[:3000] if content else ""
        except Exception: repo["readme"] = ""
        
        try:
            repo["languages"] = _safe_get(f"{GITHUB_API}/repos/{username}/{repo['name']}/languages").json()
        except Exception: repo["languages"] = {}
        
        try:
            commits = _safe_get(f"{GITHUB_API}/repos/{username}/{repo['name']}/commits", params={"author": username, "per_page": 5}).json()
            if isinstance(commits, list):
                repo["user_commits"] = [c.get("commit", {}).get("message", "").split("\n")[0] for c in commits]
            else:
                repo["user_commits"] = []
        except Exception: repo["user_commits"] = []
        
        time.sleep(0.08)

    lang_totals = {}
    for repo in repos[:20]:
        for lang, count in repo.get("languages", {}).items():
            lang_totals[lang] = lang_totals.get(lang, 0) + count

    return json.dumps({
        "profile": profile,
        "repos": repos,
        "total_stars": sum(r["stargazers_count"] for r in repos),
        "top_languages": dict(sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:10]),
    })

@mcp.tool()
def analyze_candidate(github_data_json: str, jd_text: str, prefs_json: str = "{}") -> str:
    """Single LLM call: analyzes JD, scores all repos, and computes skill gap. Returns JSON."""
    log.info("Running unified candidate analysis")
    github_data = json.loads(github_data_json)
    prefs = json.loads(prefs_json)
    model_choice = prefs.get("model_choice", "Groq (Llama 3.3 70B)")

    repos = github_data["repos"][:20]
    repo_summaries = [
        {
            "name": r["name"],
            "desc": r.get("description", "")[:100],
            "langs": list(r.get("languages", {}).keys())[:5],
            "topics": r.get("topics", [])[:5],
            "readme": r.get("readme", "")[:200],
            "commits": r.get("user_commits", [])[:3],
            "stars": r.get("stargazers_count", 0),
            "is_fork": r.get("is_fork", False),
        }
        for r in repos
    ]

    prompt = f"""You are a senior technical recruiter. Analyze this candidate's GitHub profile against a job description in a single pass.

JOB DESCRIPTION:
{jd_text[:2500]}

CANDIDATE REPOS:
{json.dumps(repo_summaries, separators=(',', ':'))}

Return a single JSON object with EXACTLY this structure — no extra keys, no markdown:
{{
  "jd_analysis": {{
    "role_title": "<job title>",
    "domain": "<e.g. ML Engineering, Backend, Full Stack>",
    "experience_level": "<Junior|Mid|Senior>",
    "required_skills": ["<specific atomic skill>"],
    "preferred_skills": ["<specific atomic skill>"],
    "technologies": ["<specific tool/framework>"]
  }},
  "scored_repos": [
    {{"name": "<repo name>", "relevance_score": <0.0-1.0>, "matched_skills": ["<matched JD skill>"]}}
  ],
  "skill_gap": {{
    "matched": ["<JD skill the candidate clearly has>"],
    "missing": ["<JD skill the candidate lacks>"]
  }}
}}

SCORING GUIDE (relevance_score):
0.8-1.0 = repo directly uses 2+ required JD skills
0.5-0.8 = repo uses 1 required skill or closely related tech
0.2-0.5 = same language or domain as JD
0.0-0.2 = unrelated

SEMANTIC MAPPINGS (use these — do NOT require exact string match):
groq/openai/langchain/huggingface/ollama/gemini → LLMs, Generative AI, NLP
pytorch/tensorflow/keras/yolov8/sklearn → Machine Learning, Deep Learning
fastapi/flask/django/express → REST APIs, Backend
docker/kubernetes/compose → DevOps, Containerization
react/vue/next.js/streamlit → Frontend, UI
mcp/fastmcp/agents/tool-calling → Agentic AI, AI Agents
git/github-actions → Version Control, CI/CD

RULES:
- scored_repos MUST include ALL {len(repo_summaries)} repos by exact name
- skill_gap: every JD skill must appear in matched OR missing (not both, not neither)
- All skills must be atomic tokens: "PyTorch" not "deep learning frameworks"
- Use repo name + commit messages as strong signals of repo purpose"""
    raw = get_llm_response(
        "You are a JSON-only technical recruiter API. Return only valid JSON, no markdown.",
        prompt, model_choice, temperature=0.1
    )
    result = json.loads(raw)

    jd_analysis = result.get("jd_analysis", {})
    score_map = {s["name"]: s for s in result.get("scored_repos", [])}

    # Merge scores back into the full repo list
    for r in github_data["repos"]:
        s = score_map.get(r["name"], {})
        r["relevance_score"] = float(s.get("relevance_score", 0.0))
        r["matched_skills"] = s.get("matched_skills", [])

    # Sort by relevance score (top 20 only — rest keep original order)
    top20_sorted = sorted(github_data["repos"][:20], key=lambda x: x.get("relevance_score", 0), reverse=True)
    ranked_repos = top20_sorted + github_data["repos"][20:]

    skill_gap = result.get("skill_gap", {"matched": [], "missing": []})
    # Sanity: ensure every required/preferred skill appears somewhere
    all_jd_skills = list(dict.fromkeys(
        jd_analysis.get("required_skills", []) + jd_analysis.get("preferred_skills", [])
    ))
    accounted = set(skill_gap.get("matched", []) + skill_gap.get("missing", []))
    for skill in all_jd_skills:
        if skill not in accounted:
            skill_gap.setdefault("missing", []).append(skill)

    log.info(f"Analysis complete: {len(ranked_repos)} repos scored, "
             f"{len(skill_gap.get('matched',[]))} matched / {len(skill_gap.get('missing',[]))} missing skills")

    return json.dumps({
        "jd_analysis": jd_analysis,
        "ranked_repos": ranked_repos,
        "skill_gap": skill_gap,
    })


@mcp.tool()
def generate_resume_content(
    github_data_json: str,
    ranked_repos_json: str,
    jd_analysis_json: str,
    prefs_json: str,
    skill_gap_json: str = "{}",
) -> str:
    """Generates professional summary, bullet points, and skills section. Returns JSON."""
    log.info("Generating resume content")
    github_data = json.loads(github_data_json)
    ranked_repos = json.loads(ranked_repos_json)
    jd_analysis = json.loads(jd_analysis_json)
    prefs = json.loads(prefs_json)
    skill_gap_pre = json.loads(skill_gap_json) if skill_gap_json else {}
    model_choice = prefs.get("model_choice", "Groq (Llama 3.3 70B)")

    original_repos = [r for r in ranked_repos if not r.get("is_fork")]
    forked_repos   = [r for r in ranked_repos if r.get("is_fork")]

    num_projects      = int(prefs.get("num_projects", 3))
    user_instructions = prefs.get("user_instructions", "").strip()
    sys_override      = (
        f"\n\nCRITICAL USER INSTRUCTIONS (override defaults):\n{user_instructions}"
        if user_instructions else ""
    )

    top_repos = original_repos[:num_projects]
    top_forks = forked_repos[:2]

    projects, contributions = [], []

    # ── Per-project bullets ────────────────────────────────────────────────
    for repo in top_repos:
        commit_ctx = (
            f"\nKey commits: {', '.join(repo.get('user_commits', [])[:3])}"
            if repo.get("user_commits") else ""
        )
        instr_block = f"USER INSTRUCTIONS (highest priority):\n{user_instructions}\n\n" if user_instructions else ""
        prompt = (
            f"{instr_block}Write resume bullet points for this GitHub project.\n"
            f"Target role: {jd_analysis.get('role_title', 'Software Engineer')}\n"
            f"Repo: {repo['name']} | Desc: {repo.get('description','')[:120]}\n"
            f"Languages: {', '.join(list(repo.get('languages', {}).keys())[:5])}\n"
            f"README: {repo.get('readme', '')[:400]}{commit_ctx}\n\n"
            f"Return JSON: {{\"bullets\": [\"<3-4 action-verb sentences>\"], "
            f"\"tech_stack\": [\"<lib/tool>\"], \"one_liner\": \"<one sentence>\"}}"
        )
        try:
            raw = get_llm_response(
                f"You are an expert resume writer. Return ONLY JSON.{sys_override}",
                prompt, model_choice, temperature=0.3
            )
            projects.append({**repo, **json.loads(raw)})
        except Exception:
            projects.append({**repo, "bullets": [f"Built {repo['name']}."],
                             "tech_stack": list(repo.get("languages", {}).keys())[:5]})

    # ── Fork contributions ─────────────────────────────────────────────────
    for repo in top_forks:
        commit_ctx = f"\nCommits: {', '.join(repo.get('user_commits', [])[:3])}" if repo.get("user_commits") else ""
        prompt = (
            f"Write ONE professional resume bullet for an open-source contribution.\n"
            f"Start with an action verb. No pronouns (I/he/she/they/user).\n"
            f"Project: {repo['name']} | Desc: {repo.get('description','')[:100]}{commit_ctx}\n"
            f"Return JSON: {{\"contribution\": \"<sentence>\"}}"
        )
        try:
            raw = get_llm_response("Return ONLY JSON.", prompt, model_choice, temperature=0.2)
            contributions.append({
                "name": repo["name"], "url": repo.get("html_url", ""),
                "contribution": json.loads(raw).get("contribution", f"Contributed to {repo['name']}.")
            })
        except Exception:
            contributions.append({"name": repo["name"], "url": repo.get("html_url", ""),
                                   "contribution": f"Contributed to {repo['name']}."})

    # ── Professional summary ───────────────────────────────────────────────
    instr_block = f"USER INSTRUCTIONS (highest priority):\n{user_instructions}\n\n" if user_instructions else ""
    sum_prompt = (
        f"{instr_block}Write a 2-3 sentence professional summary for a resume.\n"
        f"Candidate: {github_data['profile']['username']} | "
        f"Role: {jd_analysis.get('role_title', 'Software Engineer')}\n"
        f"Top languages: {list(github_data.get('top_languages', {}).keys())[:5]}\n"
        f"Top projects: {[p['name'] for p in projects[:3]]}\n"
        f"Return JSON: {{\"summary\": \"<2-3 sentences>\"}}"
    )
    try:
        raw = get_llm_response(f"Return ONLY JSON.{sys_override}", sum_prompt, model_choice, temperature=0.4)
        summary = json.loads(raw).get("summary", "")
    except Exception:
        summary = ""

    # ── Skill gap — use pre-computed from analyze_candidate if available ───
    if skill_gap_pre.get("matched") is not None:
        matched = skill_gap_pre.get("matched", [])
        missing = skill_gap_pre.get("missing", [])
        log.info(f"Using pre-computed skill gap: {len(matched)} matched, {len(missing)} missing")
    else:
        # Fallback: simple keyword match (no extra LLM call)
        log.info("No pre-computed skill gap — using keyword fallback")
        candidate_tech = set()
        for r in github_data["repos"]:
            candidate_tech.add(r.get("language", "").lower())
            candidate_tech.update(t.lower() for t in r.get("topics", []))
            candidate_tech.update(l.lower() for l in r.get("languages", {}).keys())
        for p in projects:
            candidate_tech.update(s.lower() for s in p.get("tech_stack", []))
        candidate_tech.discard("")

        jd_skills = list(dict.fromkeys(
            jd_analysis.get("required_skills", []) + jd_analysis.get("preferred_skills", [])
        ))
        matched, missing = [], []
        for skill in jd_skills:
            if any(skill.lower() in t or t in skill.lower() for t in candidate_tech if t):
                matched.append(skill)
            else:
                missing.append(skill)

    return json.dumps({
        "summary": summary,
        "projects": projects,
        "contributions": contributions,
        "skills_section": {
            "Languages": list(github_data.get("top_languages", {}).keys())[:10],
            "Technologies": list(dict.fromkeys(s for p in projects for s in p.get("tech_stack", [])))[:12],
            "Tools": [t for t in jd_analysis.get("technologies", [])
                      if t not in list(github_data.get("top_languages", {}).keys())][:8],
        },
        "skill_gap": {"matched": matched, "missing": missing},
        "profile": github_data["profile"],
        "jd_analysis": jd_analysis,
        "preferences": prefs,
    })


if __name__ == "__main__":
    mcp.run()

