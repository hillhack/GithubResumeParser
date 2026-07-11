"""
github_api.py — GitHub API client.
Handles repo listing and deterministic repo enrichment (languages, deps, topics, README).
All network calls are disk-cached with a 24-hour TTL.
"""

import os
import base64
import requests
from typing import List, Dict, Any
from cache import get_cached, set_cached


def _gh_headers() -> dict:
    """Build GitHub API headers, adding token if available."""
    headers = {"Accept": "application/vnd.github.v3+json"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def fetch_github_repos(username: str) -> Dict[str, List[Dict[str, str]]]:
    """
    Fetch public repositories for a given GitHub username.
    Returns a dict with 'own_repos' and 'oss_repos' (forks).
    Results are cached for 24 hours.
    """
    if not username:
        return {"own_repos": [], "oss_repos": []}

    cache_key = f"repos:{username}"
    cached = get_cached("github_repos", cache_key)
    if cached:
        return cached

    url = f"https://api.github.com/users/{username}/repos"
    params = {"type": "owner", "sort": "updated", "per_page": 100}

    try:
        resp = requests.get(url, headers=_gh_headers(), params=params, timeout=10)

        if resp.status_code == 404:
            raise ValueError(f"GitHub user '{username}' not found.")
        elif resp.status_code == 403 and "rate limit" in resp.text.lower():
            raise ValueError("GitHub API rate limit exceeded. Add a GitHub Token in Settings for higher limits.")

        resp.raise_for_status()

        own_repos, oss_repos = [], []
        for repo in resp.json():
            info = {
                "name":        repo.get("name", ""),
                "url":         repo.get("html_url", ""),
                "description": repo.get("description") or "No description provided.",
                "topics":      repo.get("topics", []),
            }
            if repo.get("fork"):
                oss_repos.append(info)
            else:
                own_repos.append(info)

        result = {"own_repos": own_repos, "oss_repos": oss_repos}
        set_cached("github_repos", cache_key, result)
        return result

    except requests.exceptions.HTTPError as e:
        err_msg = ""
        try:
            err_msg = e.response.json().get('message', e.response.text)
        except:
            err_msg = e.response.text
        raise ValueError(f"GitHub API Error {e.response.status_code}: {err_msg}")
    except requests.RequestException as e:
        raise ValueError(f"Network error fetching repositories. (Error: {type(e).__name__})")


def fetch_user_contributions(username: str) -> List[Dict[str, str]]:
    """
    Fetch the user's REAL contributions to external (non-own) repos:
    1. Merged Pull Requests authored by the user to repos they don't own.
    2. Push/commit events to external repos via the events API.

    Returns list of dicts: {repo, repo_url, pr_url, title, type}
    Cached for 24 hours.
    """
    if not username:
        return []

    cache_key = f"contributions:{username}"
    cached = get_cached("github_contributions", cache_key)
    if cached:
        return cached

    contributions: List[Dict[str, str]] = []
    seen_repos: set = set()

    # ── 1. Merged PRs via Search API ─────────────────────────────────────────
    try:
        resp = requests.get(
            "https://api.github.com/search/issues",
            headers=_gh_headers(),
            params={"q": f"author:{username} type:pr is:merged -user:{username}",
                    "sort": "updated", "per_page": 30},
            timeout=15
        )
        if resp.ok:
            for item in resp.json().get("items", []):
                repo_full = item.get("repository_url", "").replace(
                    "https://api.github.com/repos/", "")
                if repo_full.startswith(f"{username}/"):
                    continue
                key = repo_full
                if key not in seen_repos:
                    seen_repos.add(key)
                    contributions.append({
                        "repo":     repo_full.split("/")[-1],
                        "repo_url": f"https://github.com/{repo_full}",
                        "pr_url":   item.get("html_url", ""),
                        "title":    item.get("title", "Merged PR"),
                        "type":     "Merged PR",
                    })
    except requests.RequestException:
        pass

    # ── 2. Push/PR events to external repos (public activity feed) ───────────
    try:
        resp = requests.get(
            f"https://api.github.com/users/{username}/events/public",
            headers=_gh_headers(),
            params={"per_page": 100},
            timeout=15
        )
        if resp.ok:
            for event in resp.json():
                if event.get("type") not in ("PushEvent", "PullRequestEvent"):
                    continue
                repo_full = event.get("repo", {}).get("name", "")
                if not repo_full or repo_full.startswith(f"{username}/"):
                    continue
                if repo_full in seen_repos:
                    continue
                seen_repos.add(repo_full)
                payload = event.get("payload", {})
                if event["type"] == "PushEvent":
                    commits = payload.get("commits", [])
                    desc = commits[0].get("message", "Push")[:100] if commits else "Push"
                    contributions.append({
                        "repo":     repo_full.split("/")[-1],
                        "repo_url": f"https://github.com/{repo_full}",
                        "pr_url":   "",
                        "title":    desc,
                        "type":     "Commit",
                    })
                else:
                    pr = payload.get("pull_request", {})
                    contributions.append({
                        "repo":     repo_full.split("/")[-1],
                        "repo_url": f"https://github.com/{repo_full}",
                        "pr_url":   pr.get("html_url", ""),
                        "title":    pr.get("title", "Pull Request"),
                        "type":     f"PR ({payload.get('action', '')})",
                    })
    except requests.RequestException:
        pass

    set_cached("github_contributions", cache_key, contributions)
    return contributions


# ─── Dependency file candidates ──────────────────────────────────────────────
_DEP_FILES = [
    "requirements.txt",
    "requirements-dev.txt",
    "environment.yml",
    "pyproject.toml",
    "setup.py",
    "setup.cfg",
    "Pipfile",
    "package.json",
    "pom.xml",
    "build.gradle",
    "Cargo.toml",
    "go.mod",
    # Common source files to extract raw imports
    "app.py",
    "main.py",
    "index.py",
    "index.js",
    "server.js",
]

def _fetch_text_file(owner: str, repo: str, path: str) -> str | None:
    """Try to fetch a single file from a repo. Returns text content or None."""
    url = f"https://api.github.com/repos/{owner}/{repo}/contents/{path}"
    try:
        resp = requests.get(url, headers=_gh_headers(), timeout=15)
        if resp.status_code != 200:
            return None
        data = resp.json()
        if data.get("encoding") == "base64":
            try:
                return base64.b64decode(data["content"]).decode("utf-8", errors="ignore")
            except Exception:
                return None
        return data.get("content")
    except requests.exceptions.Timeout:
        return None   # silently skip — slow GitHub response, not a user error
    except requests.RequestException:
        return None   # silently skip — non-fatal


def _fetch_languages(owner: str, repo: str) -> Dict[str, int]:
    """Fetch language breakdown (name → bytes) for a repo."""
    url = f"https://api.github.com/repos/{owner}/{repo}/languages"
    try:
        resp = requests.get(url, headers=_gh_headers(), timeout=15)
        if resp.ok:
            return resp.json()
        return {}
    except requests.exceptions.Timeout:
        return {}   # silently skip
    except requests.RequestException:
        return {}


def _parse_dep_names(filename: str, content: str) -> List[str]:
    """
    Extract library/package names from common dependency file formats.
    Purely string-based — no external parsing libraries required.
    """
    names: List[str] = []

    if filename in ("requirements.txt", "requirements-dev.txt"):
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip version specifiers: numpy>=1.20 → numpy
            for sep in (">=", "<=", "==", "!=", "~=", ">", "<", "[", ";", "@"):
                line = line.split(sep)[0]
            name = line.strip()
            if name:
                names.append(name.lower())

    elif filename == "package.json":
        import json as _json
        try:
            pkg = _json.loads(content)
            for section in ("dependencies", "devDependencies"):
                names.extend(k.lower() for k in pkg.get(section, {}).keys())
        except Exception:
            pass

    elif filename == "pyproject.toml":
        for line in content.splitlines():
            line = line.strip().strip('"').strip("'")
            if not line or line.startswith("[") or line.startswith("#"):
                continue
            for sep in (">=", "<=", "==", "[", ";"):
                line = line.split(sep)[0]
            name = line.strip()
            if name and not name.startswith("-"):
                names.append(name.lower())

    elif filename == "go.mod":
        for line in content.splitlines():
            parts = line.strip().split()
            if parts and parts[0] not in ("module", "go", "require", "//"):
                names.append(parts[0].split("/")[-1].lower())

    elif filename in ("pom.xml", "build.gradle", "Cargo.toml", "setup.py", "setup.cfg", "Pipfile"):
        import re
        patterns = [
            r'artifactId[>\s:="]+([a-z0-9_\-\.]+)',   # Maven
            r'compile["\s(]+([a-z0-9_\-\.]+)',          # Gradle
            r'dependencies\s*=\s*\[([^\]]+)\]',         # Cargo
            r'install_requires\s*=\s*\[([^\]]+)\]',     # setup.py
        ]
        for pat in patterns:
            for match in re.findall(pat, content, re.IGNORECASE):
                for item in match.split(","):
                    name = item.strip().strip('"\'').split(">=")[0].strip()
                    if name:
                        names.append(name.lower())

    elif filename == "environment.yml":
        import re
        for line in content.splitlines():
            line = line.strip()
            if line.startswith("-") and not line.startswith("- pip"):
                name = line.lstrip("- ").split("=")[0].split(">")[0].split("<")[0].strip()
                if name and name.lower() not in ("python", "pip"):
                    names.append(name.lower())

    elif filename.endswith(".py"):
        import re
        for match in re.findall(r'^import\s+([a-zA-Z0-9_,\s]+)', content, re.MULTILINE):
            for m in match.split(","):
                names.append(m.strip().split()[0].lower())
        for match in re.findall(r'^from\s+([a-zA-Z0-9_]+)\s+import', content, re.MULTILINE):
            names.append(match.strip().lower())
            
    elif filename.endswith(".js"):
        import re
        for match in re.findall(r'require\([\'"]([^\'"]+)[\'"]\)', content):
            if not match.startswith("."): 
                names.append(match.split("/")[0].lower())
        for match in re.findall(r'from\s+[\'"]([^\'"]+)[\'"]', content):
            if not match.startswith("."):
                names.append(match.split("/")[0].lower())

    return [n for n in names if n and len(n) > 1]


def enrich_repo(owner: str, repo_name: str) -> Dict[str, Any]:
    """
    Deterministically enrich a single GitHub repo with:
    - languages (dict name→bytes)
    - topics (list of strings)
    - dependencies (list of canonical library names)
    - readme_text (raw README.md content, up to 8000 chars)
    Results are cached for 24 hours.
    """
    cache_key = f"enrich:{owner}/{repo_name}"
    cached = get_cached("github_enrich", cache_key)
    if cached:
        return cached

    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Fetch languages + README + all dep files in parallel
    def _fetch_readme():
        for readme_path in ("README.md", "readme.md", "README.rst", "README"):
            content = _fetch_text_file(owner, repo_name, readme_path)
            if content:
                return content[:8000]
        return ""

    def _fetch_dep(dep_file):
        content = _fetch_text_file(owner, repo_name, dep_file)
        if content:
            return dep_file, content
        return dep_file, None

    with ThreadPoolExecutor(max_workers=10) as ex:
        lang_future    = ex.submit(_fetch_languages, owner, repo_name)
        readme_future  = ex.submit(_fetch_readme)
        dep_futures    = {ex.submit(_fetch_dep, f): f for f in _DEP_FILES}

        languages  = lang_future.result()
        readme_text = readme_future.result()

        dependencies: List[str] = []
        dep_files_found: List[str] = []
        for future in as_completed(dep_futures):
            dep_file, content = future.result()
            if content:
                dep_files_found.append(dep_file)
                dependencies.extend(_parse_dep_names(dep_file, content))

    # Deduplicate raw names
    dependencies = list(dict.fromkeys(dependencies))

    result = {
        "languages":       languages,
        "topics":          [],   # topics fetched during repo listing
        "dependencies":    dependencies,
        "readme_text":     readme_text,
        "dep_files_found": dep_files_found,
    }
    set_cached("github_enrich", cache_key, result)
    return result
