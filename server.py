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

mcp = FastMCP("GithubResumeParser")

GITHUB_API = "https://api.github.com"
_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
AUTH = (_CLIENT_ID, _CLIENT_SECRET) if _CLIENT_ID else None

def get_groq_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not set in environment")
    return Groq(api_key=api_key)

def _safe_get(url: str, params: dict | None = None) -> requests.Response:
    try:
        resp = requests.get(url, auth=AUTH, timeout=15, params=params or {})
        resp.raise_for_status()
        return resp
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
            if r.get("fork"): continue
            repos.append({
                "name": r["name"],
                "description": r.get("description") or "",
                "html_url": r.get("html_url", ""),
                "topics": r.get("topics", []),
                "language": r.get("language") or "",
                "stargazers_count": r.get("stargazers_count", 0),
                "forks_count": r.get("forks_count", 0),
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
def analyze_job_description(jd_text: str) -> str:
    """Extracts required skills, domain, and experience level from a job description. Returns JSON."""
    log.info("Analyzing job description")
    client = get_groq_client()
    sys_prompt = "You are an expert technical recruiter. Extract structured information from job descriptions. Return ONLY valid JSON."
    user_prompt = f"""Analyze this job description and return a JSON object with: role_title, domain, experience_level, required_skills (list), preferred_skills (list), technologies (list). JD: {jd_text[:4000]}"""
    
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "system", "content": sys_prompt}, {"role": "user", "content": user_prompt}],
        temperature=0.1, response_format={"type": "json_object"}
    )
    return resp.choices[0].message.content or "{}"

@mcp.tool()
def score_repositories(repos_json: str, jd_analysis_json: str) -> str:
    """Scores a list of repositories against a job description for relevance. Expects JSON strings. Returns JSON."""
    log.info("Scoring repositories")
    repos = json.loads(repos_json)
    jd_analysis = json.loads(jd_analysis_json)
    client = get_groq_client()

    if not repos:
        return json.dumps(repos)

    # Build JD keyword set for fallback keyword scoring
    jd_keywords = set()
    for skill in jd_analysis.get("required_skills", []) + jd_analysis.get("preferred_skills", []) + jd_analysis.get("technologies", []):
        jd_keywords.update(skill.lower().split())
    jd_keywords.discard("")

    def _keyword_score(repo: dict) -> tuple[float, list[str]]:
        """Fallback: score repo by keyword overlap with JD."""
        repo_text = " ".join([
            repo.get("name", ""),
            repo.get("description", ""),
            repo.get("language", ""),
            " ".join(repo.get("topics", [])),
            " ".join(repo.get("languages", {}).keys()),
            repo.get("readme", "")[:800],
        ]).lower()
        hits = [kw for kw in jd_keywords if kw in repo_text and len(kw) > 2]
        score = min(len(hits) / max(len(jd_keywords), 1), 1.0)
        return round(score, 3), hits

    score_map: dict[str, dict] = {}
    batch_size = 12

    for i in range(0, len(repos), batch_size):
        batch = repos[i : i + batch_size]
        summaries = [
            {
                "name": r["name"],
                "description": r.get("description", "")[:200],
                "topics": r.get("topics", []),
                "languages": list(r.get("languages", {}).keys())[:6],
                "readme_snippet": r.get("readme", "")[:600],
            }
            for r in batch
        ]

        prompt = f"""You are a technical recruiter. Score each repository for relevance to the target role.

Target Role: {jd_analysis.get('role_title')}
Domain: {jd_analysis.get('domain')}
Required Skills: {jd_analysis.get('required_skills')}
Preferred Skills: {jd_analysis.get('preferred_skills')}

Repositories to score:
{json.dumps(summaries, indent=2)}

Return ONLY a JSON object in this exact format:
{{"results": [{{
  "name": "<repo name>",
  "relevance_score": <float 0.0-1.0>,
  "matched_skills": ["<skill1>", "<skill2>"]
}}]}}

Be generous — if a repo uses any relevant technology, give it at least 0.1. Score 0 ONLY if completely unrelated."""

        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a JSON-only API. Always return the exact JSON format requested."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            log.info(f"Scoring batch {i}: parsed keys = {list(parsed.keys())[:5]}")

            # Try the expected key first, then any list value found in the object
            scores = parsed.get("results", [])
            if not scores:
                for v in parsed.values():
                    if isinstance(v, list) and v and isinstance(v[0], dict) and "name" in v[0]:
                        scores = v
                        break

            for s in scores:
                name = s.get("name", "")
                if name:
                    score_map[name] = {
                        "relevance_score": float(s.get("relevance_score", 0.0)),
                        "matched_skills": s.get("matched_skills", []),
                    }
        except Exception as e:
            log.error(f"LLM scoring batch {i} failed: {e}. Using keyword fallback.")

    # Apply scores — use keyword fallback for any repo the LLM missed
    for r in repos:
        if r["name"] in score_map:
            r["relevance_score"] = score_map[r["name"]]["relevance_score"]
            r["matched_skills"] = score_map[r["name"]]["matched_skills"]
        else:
            fb_score, fb_skills = _keyword_score(r)
            r["relevance_score"] = fb_score
            r["matched_skills"] = fb_skills
            log.info(f"Keyword fallback for '{r['name']}': {fb_score:.2f}")

    return json.dumps(repos)

@mcp.tool()
def generate_resume_content(github_data_json: str, ranked_repos_json: str, jd_analysis_json: str, prefs_json: str) -> str:
    """Generates professional summary, bullet points, and skills section for the resume. Expects JSON strings. Returns JSON."""
    log.info("Generating resume content")
    github_data = json.loads(github_data_json)
    ranked_repos = json.loads(ranked_repos_json)
    jd_analysis = json.loads(jd_analysis_json)
    prefs = json.loads(prefs_json)
    client = get_groq_client()
    
    pages = prefs.get("pages", 1)
    top_repos = ranked_repos[:4 if pages == 1 else 7]
    projects = []
    
    # Bullets
    for repo in top_repos:
        prompt = f"""Generate resume content for this GitHub project targeting {jd_analysis.get('role_title')}.
Project: {repo['name']}
Desc: {repo.get('description')}
Tech: {', '.join(list(repo.get('languages', {}).keys())[:6])}
README: {repo.get('readme', '')[:600]}
Return JSON with: bullets (list of action-verb sentences), tech_stack (list), one_liner (str)."""
        try:
            resp = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "You are a resume writer. Return ONLY JSON."}, {"role": "user", "content": prompt}],
                temperature=0.3, response_format={"type": "json_object"}
            )
            content = json.loads(resp.choices[0].message.content or "{}")
            projects.append({**repo, **content})
        except Exception:
            projects.append({**repo, "bullets": [f"Developed {repo['name']}"], "tech_stack": list(repo.get("languages", {}).keys())[:5]})

    # Summary
    sum_prompt = f"""Write a 2-3 sentence resume summary for GitHub user {github_data['profile']['username']}. 
Target Role: {jd_analysis.get('role_title')}. Top langs: {list(github_data.get('top_languages', {}).keys())[:5]}.
Return JSON: {{"summary": "..."}}"""
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Return ONLY JSON."}, {"role": "user", "content": sum_prompt}],
            temperature=0.4, response_format={"type": "json_object"}
        )
        summary = json.loads(resp.choices[0].message.content or "{}").get("summary", "")
    except Exception: summary = ""

    # Skills gap
    candidate_tech = set()
    for r in github_data["repos"]:
        candidate_tech.add(r.get("language", "").lower())
        candidate_tech.update(t.lower() for t in r.get("topics", []))
        candidate_tech.update(l.lower() for l in r.get("languages", {}).keys())
    candidate_tech.update(l.lower() for l in github_data.get("top_languages", {}).keys())
    
    matched, missing = [], []
    for skill in jd_analysis.get("required_skills", []) + jd_analysis.get("preferred_skills", []):
        if any(skill.lower() in t or t in skill.lower() for t in candidate_tech if t):
            matched.append(skill)
        elif skill in jd_analysis.get("required_skills", []):
            missing.append(skill)

    return json.dumps({
        "summary": summary,
        "projects": projects,
        "skills_section": {
            "Languages": list(github_data.get("top_languages", {}).keys())[:10],
            "Technologies": list(set(s for p in projects for s in p.get("tech_stack", [])))[:12],
            "Tools": [t for t in jd_analysis.get("technologies", []) if t not in list(github_data.get("top_languages", {}).keys())][:8]
        },
        "skill_gap": {"matched": matched, "missing": missing, "candidate_tech": sorted(list(candidate_tech - {""}))},
        "profile": github_data["profile"],
        "jd_analysis": jd_analysis,
        "preferences": prefs
    })

if __name__ == "__main__":
    mcp.run()
