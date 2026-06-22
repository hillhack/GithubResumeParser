"""Repository scoring and ranking against a job description."""

import json
import logging
from typing import Any

from groq import Groq

log = logging.getLogger(__name__)

_SYSTEM = """You are a technical recruiter scoring GitHub repositories for relevance to a job description.
Return ONLY valid JSON — no markdown fences, no commentary."""

_RANK_PROMPT = """Score each repository for relevance to the job description below.
For each repo, analyze: description, topics, languages, and README snippet.

Job Description context:
- Role: {role_title}
- Domain: {domain}
- Required skills: {required_skills}
- Technologies: {technologies}

Repositories to score:
{repos_json}

Return a JSON array where each object has:
{{
  "name": "repo_name",
  "relevance_score": 0.00-1.00,
  "matched_skills": ["skill1"],
  "reason": "one sentence explanation"
}}

Order doesn't matter. Include all repos."""


def _repo_summary(repo: dict[str, Any]) -> dict[str, Any]:
    """Compact repo summary for LLM prompt (token-efficient)."""
    langs = list((repo.get("languages") or {}).keys())[:5]
    readme_snippet = (repo.get("readme") or "")[:500]
    return {
        "name": repo["name"],
        "description": repo.get("description", "")[:200],
        "topics": repo.get("topics", [])[:10],
        "language": repo.get("language", ""),
        "languages": langs,
        "stars": repo.get("stargazers_count", 0),
        "readme_snippet": readme_snippet,
    }


def score_repos_with_jd(
    repos: list[dict[str, Any]],
    jd_analysis: dict[str, Any],
    client: Groq,
    model: str = "llama-3.3-70b-versatile",
    batch_size: int = 15,
) -> list[dict[str, Any]]:
    """
    Score repos for JD relevance using Groq LLM in batches.
    Returns repos list with 'relevance_score', 'matched_skills', 'reason' added.
    """
    if not repos:
        return repos

    score_map: dict[str, dict[str, Any]] = {}

    for i in range(0, len(repos), batch_size):
        batch = repos[i : i + batch_size]
        summaries = [_repo_summary(r) for r in batch]
        prompt = _RANK_PROMPT.format(
            role_title=jd_analysis.get("role_title", ""),
            domain=jd_analysis.get("domain", ""),
            required_skills=", ".join(jd_analysis.get("required_skills", [])),
            technologies=", ".join(jd_analysis.get("technologies", [])),
            repos_json=json.dumps(summaries, indent=2)[:6000],
        )
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _SYSTEM},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=2048,
                response_format={"type": "json_object"},
            )
            raw = resp.choices[0].message.content or "{}"
            parsed = json.loads(raw)
            # Handle both {"scores": [...]} and direct array
            if isinstance(parsed, list):
                scores = parsed
            else:
                scores = parsed.get("scores", parsed.get("repositories", parsed.get("repos", [])))
                if not isinstance(scores, list):
                    # Try to find any list value
                    for v in parsed.values():
                        if isinstance(v, list):
                            scores = v
                            break
                    else:
                        scores = []
            for s in scores:
                name = s.get("name", "")
                if name:
                    score_map[name] = {
                        "relevance_score": float(s.get("relevance_score", 0.0)),
                        "matched_skills": s.get("matched_skills", []),
                        "reason": s.get("reason", ""),
                    }
        except Exception as e:
            log.error("Scoring batch %d failed: %s", i // batch_size, e)

    # Merge scores back into repos
    for repo in repos:
        info = score_map.get(repo["name"], {})
        repo["relevance_score"] = info.get("relevance_score", 0.0)
        repo["matched_skills"] = info.get("matched_skills", [])
        repo["relevance_reason"] = info.get("reason", "")

    return repos


def rank_by_jd(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort repos by JD relevance score descending."""
    return sorted(repos, key=lambda r: r.get("relevance_score", 0.0), reverse=True)


def rank_by_popularity(repos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Sort repos by a weighted popularity score (stars, forks, watchers)."""
    def pop_score(r: dict[str, Any]) -> float:
        return (
            r.get("stargazers_count", 0) * 1.0
            + r.get("forks_count", 0) * 0.75
            + r.get("watchers_count", 0) * 0.25
        )
    return sorted(repos, key=pop_score, reverse=True)
