"""Resume content generation using Groq LLM."""

import json
import logging
from typing import Any

from groq import Groq

log = logging.getLogger(__name__)

_SYSTEM = """You are an expert technical resume writer with 10+ years experience helping engineers
land roles at top tech companies. You write concise, impactful, ATS-optimized resume content.
Return ONLY valid JSON — no markdown fences, no commentary."""


def _generate_project_bullets(
    repo: dict[str, Any],
    jd_analysis: dict[str, Any],
    client: Groq,
    model: str,
) -> dict[str, Any]:
    """Generate resume bullet points for a single repo."""
    readme = (repo.get("readme") or "")[:1000]
    langs = list((repo.get("languages") or {}).keys())[:6]
    topics = repo.get("topics", [])[:8]

    prompt = f"""Generate resume content for this GitHub project targeting the role below.

Project: {repo['name']}
Description: {repo.get('description', 'No description')}
Languages: {', '.join(langs) or repo.get('language', 'Unknown')}
Topics/Tags: {', '.join(topics)}
Stars: {repo.get('stargazers_count', 0)}
README snippet: {readme[:600]}

Target Role: {jd_analysis.get('role_title', 'Software Engineer')}
Domain: {jd_analysis.get('domain', '')}
Key skills needed: {', '.join(jd_analysis.get('required_skills', [])[:8])}

Return JSON with:
{{
  "bullets": ["action verb + what + result/impact (max 15 words each)", "...", "..."],
  "tech_stack": ["tech1", "tech2"],
  "one_liner": "single punchy sentence describing the project"
}}

Rules:
- 2-4 bullets, each starting with a strong action verb
- Quantify impact where reasonable (users, speed, accuracy, etc.)
- Include relevant technologies from the JD when truthful
- Keep bullets under 120 characters"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=512,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        return json.loads(raw)
    except Exception as e:
        log.error("Bullet gen failed for %s: %s", repo["name"], e)
        return {
            "bullets": [f"Developed {repo['name']} using {repo.get('language', 'Python')}"],
            "tech_stack": langs,
            "one_liner": repo.get("description", ""),
        }


def generate_summary(
    profile: dict[str, Any],
    jd_analysis: dict[str, Any],
    top_repos: list[dict[str, Any]],
    client: Groq,
    model: str,
) -> str:
    """Generate a tailored professional summary."""
    repo_names = [r["name"] for r in top_repos[:5]]
    top_langs = list((profile.get("top_languages") or {}).keys())[:6]

    prompt = f"""Write a 2-3 sentence professional summary for a resume.

Candidate:
- GitHub: @{profile.get('username', '')}
- Bio: {profile.get('bio', '')}
- Top languages: {', '.join(top_langs)}
- Notable projects: {', '.join(repo_names)}
- Followers: {profile.get('followers', 0)}

Target Role: {jd_analysis.get('role_title', 'Software Engineer')}
Domain: {jd_analysis.get('domain', '')}
Required skills: {', '.join(jd_analysis.get('required_skills', [])[:8])}

Rules:
- Start with a role descriptor, not "I"
- Mention 2-3 relevant technologies
- Sound confident and specific
- Under 60 words total

Return JSON: {{"summary": "..."}}"""

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": _SYSTEM},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
            max_tokens=200,
            response_format={"type": "json_object"},
        )
        raw = resp.choices[0].message.content or "{}"
        return json.loads(raw).get("summary", "")
    except Exception as e:
        log.error("Summary generation failed: %s", e)
        return f"Software engineer with expertise in {', '.join(top_langs[:3])}."


def compute_skill_gap(
    github_data: dict[str, Any],
    jd_analysis: dict[str, Any],
) -> dict[str, list[str]]:
    """Compare JD requirements against GitHub evidence."""
    # Gather all tech signals from repos
    candidate_tech: set[str] = set()
    for repo in github_data.get("repos", []):
        candidate_tech.add(repo.get("language", "").lower())
        for topic in repo.get("topics", []):
            candidate_tech.add(topic.lower())
        for lang in (repo.get("languages") or {}).keys():
            candidate_tech.add(lang.lower())

    for lang in (github_data.get("top_languages") or {}).keys():
        candidate_tech.add(lang.lower())

    required = jd_analysis.get("required_skills", [])
    preferred = jd_analysis.get("preferred_skills", [])
    all_needed = required + preferred

    matched, missing = [], []
    for skill in all_needed:
        skill_lower = skill.lower()
        # Fuzzy-ish match
        found = any(
            skill_lower in tech or tech in skill_lower
            for tech in candidate_tech
            if tech
        )
        if found:
            matched.append(skill)
        elif skill in required:
            missing.append(skill)

    return {
        "matched": matched,
        "missing": missing,
        "candidate_tech": sorted(candidate_tech - {""}),
    }


def generate_full_resume(
    github_data: dict[str, Any],
    ranked_repos: list[dict[str, Any]],
    jd_analysis: dict[str, Any],
    preferences: dict[str, Any],
    client: Groq,
    model: str = "llama-3.3-70b-versatile",
) -> dict[str, Any]:
    """
    Orchestrate all resume generation steps.

    Returns:
    {
        "summary": str,
        "projects": [{"name", "url", "one_liner", "bullets", "tech_stack", "stars", "score"}],
        "skills_section": {"Languages": [...], "Frameworks": [...], ...},
        "skill_gap": {"matched": [...], "missing": [...]},
        "profile": {...},
    }
    """
    pages = preferences.get("pages", 1)
    project_count = 4 if pages == 1 else 7
    top_repos = ranked_repos[:project_count]

    # Generate bullets for each top repo
    projects = []
    for repo in top_repos:
        content = _generate_project_bullets(repo, jd_analysis, client, model)
        projects.append({
            "name": repo["name"],
            "url": repo.get("html_url", ""),
            "homepage": repo.get("homepage", ""),
            "description": repo.get("description", ""),
            "one_liner": content.get("one_liner", repo.get("description", "")),
            "bullets": content.get("bullets", []),
            "tech_stack": content.get("tech_stack", []),
            "stars": repo.get("stargazers_count", 0),
            "relevance_score": repo.get("relevance_score", 0.0),
            "matched_skills": repo.get("matched_skills", []),
        })

    # Summary
    profile = github_data["profile"]
    summary = generate_summary(profile, jd_analysis, top_repos, client, model)

    # Skills section (grouped)
    top_langs = list((github_data.get("top_languages") or {}).keys())[:10]
    matched_tech = list(set(
        skill for repo in top_repos for skill in repo.get("tech_stack", [])
    ))
    skills_section = {
        "Languages": top_langs,
        "Technologies": matched_tech[:12],
        "Tools": [t for t in jd_analysis.get("technologies", []) if t not in top_langs][:8],
    }

    # Skill gap
    skill_gap = compute_skill_gap(github_data, jd_analysis)

    return {
        "summary": summary,
        "projects": projects,
        "skills_section": skills_section,
        "skill_gap": skill_gap,
        "profile": profile,
        "jd_analysis": jd_analysis,
        "preferences": preferences,
    }
