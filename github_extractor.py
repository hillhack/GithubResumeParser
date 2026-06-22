"""GitHub data extraction for GithubResumeParser."""

import base64
import logging
import os
import time
from typing import Any

import requests
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger(__name__)

GITHUB_API = "https://api.github.com"
_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
AUTH = (_CLIENT_ID, _CLIENT_SECRET) if _CLIENT_ID else None


def _safe_get(url: str, params: dict | None = None) -> requests.Response:
    """GET with auth, timeout, and error handling."""
    try:
        resp = requests.get(url, auth=AUTH, timeout=15, params=params or {})
        remaining = int(resp.headers.get("X-RateLimit-Remaining", 999))
        if remaining < 10:
            log.warning("GitHub rate limit low: %d remaining", remaining)
        resp.raise_for_status()
        return resp
    except requests.HTTPError as e:
        log.error("HTTP error %s: %s", url, e)
        raise
    except requests.RequestException as e:
        log.error("Request error %s: %s", url, e)
        raise


def get_user_profile(username: str) -> dict[str, Any]:
    """Fetch GitHub user profile fields."""
    data = _safe_get(f"{GITHUB_API}/users/{username}").json()
    return {
        "username": data.get("login", username),
        "name": data.get("name") or username,
        "bio": data.get("bio") or "",
        "location": data.get("location") or "",
        "email": data.get("email") or "",
        "blog": data.get("blog") or "",
        "company": data.get("company") or "",
        "public_repos": data.get("public_repos", 0),
        "followers": data.get("followers", 0),
        "avatar_url": data.get("avatar_url", ""),
        "html_url": data.get("html_url", ""),
        "created_at": data.get("created_at", ""),
    }


def get_repositories(username: str, max_repos: int = 60) -> list[dict[str, Any]]:
    """Fetch non-fork repositories sorted by stars."""
    repos: list[dict[str, Any]] = []
    page = 1
    while len(repos) < max_repos:
        batch = _safe_get(
            f"{GITHUB_API}/users/{username}/repos",
            params={"per_page": 100, "sort": "updated", "page": page},
        ).json()
        if not batch:
            break
        for r in batch:
            if r.get("fork"):
                continue
            repos.append({
                "name": r["name"],
                "full_name": r["full_name"],
                "description": r.get("description") or "",
                "html_url": r.get("html_url", ""),
                "topics": r.get("topics", []),
                "language": r.get("language") or "",
                "stargazers_count": r.get("stargazers_count", 0),
                "forks_count": r.get("forks_count", 0),
                "watchers_count": r.get("watchers_count", 0),
                "size": r.get("size", 0),
                "created_at": r.get("created_at", ""),
                "updated_at": r.get("updated_at", ""),
                "homepage": r.get("homepage") or "",
                "license": (r.get("license") or {}).get("name", ""),
                "open_issues_count": r.get("open_issues_count", 0),
            })
        page += 1
        if len(batch) < 100:
            break
    repos.sort(key=lambda r: r["stargazers_count"], reverse=True)
    return repos[:max_repos]


def get_repo_readme(username: str, repo_name: str) -> str:
    """Fetch and decode README content (first 3000 chars)."""
    try:
        data = _safe_get(f"{GITHUB_API}/repos/{username}/{repo_name}/readme").json()
        content = data.get("content", "")
        if content:
            return base64.b64decode(content).decode("utf-8", errors="replace")[:3000]
    except Exception:
        pass
    return ""


def get_repo_languages(username: str, repo_name: str) -> dict[str, int]:
    """Fetch language byte-count breakdown for a repo."""
    try:
        return _safe_get(f"{GITHUB_API}/repos/{username}/{repo_name}/languages").json()
    except Exception:
        return {}


def enrich_repositories(
    username: str, repos: list[dict[str, Any]], top_n: int = 20
) -> list[dict[str, Any]]:
    """Add README and language data to the top N repos."""
    for repo in repos[:top_n]:
        repo["readme"] = get_repo_readme(username, repo["name"])
        repo["languages"] = get_repo_languages(username, repo["name"])
        time.sleep(0.08)
    for repo in repos[top_n:]:
        repo["readme"] = ""
        repo["languages"] = {}
    return repos


def extract_full_profile(username: str) -> dict[str, Any]:
    """
    Main entry point. Returns:
    {
        "profile": {...},
        "repos": [...],
        "total_stars": int,
        "top_languages": {lang: bytes, ...},
    }
    """
    profile = get_user_profile(username)
    repos = get_repositories(username)
    repos = enrich_repositories(username, repos)

    lang_totals: dict[str, int] = {}
    for repo in repos:
        for lang, count in repo.get("languages", {}).items():
            lang_totals[lang] = lang_totals.get(lang, 0) + count

    return {
        "profile": profile,
        "repos": repos,
        "total_stars": sum(r["stargazers_count"] for r in repos),
        "top_languages": dict(
            sorted(lang_totals.items(), key=lambda x: x[1], reverse=True)[:10]
        ),
    }
