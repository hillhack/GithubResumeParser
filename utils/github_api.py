import os
import requests
import base64
from typing import Optional, Dict, Any, List
from .constants import GITHUB_API_URL
from .cache import disk_cache
from datetime import datetime

def _headers(token: str = None) -> dict:
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "alldone-github-resume/2.0",
    }
    token = token or os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers

def _check_rate_limit(resp):
    if resp.status_code == 403:
        reset_time = resp.headers.get("X-RateLimit-Reset")
        if reset_time:
            reset_dt = datetime.fromtimestamp(int(reset_time))
            time_str = reset_dt.strftime('%I:%M %p')
            raise RuntimeError(f"GitHub API Rate Limit Exceeded. It will renew at {time_str}. Please add a valid GITHUB_TOKEN to your .env file to increase limits.")
        raise RuntimeError("GitHub API Rate Limit Exceeded. Please add a valid GITHUB_TOKEN to your .env file. Unauthenticated users are limited to 60 requests per hour.")
    resp.raise_for_status()

@disk_cache(namespace="gh_user")
def get_user(username: str, token: str = None) -> Dict[str, Any]:
    url = f"{GITHUB_API_URL}/users/{username}"
    resp = requests.get(url, headers=_headers(token), timeout=15)
    _check_rate_limit(resp)
    return resp.json()

@disk_cache(namespace="gh_repos")
def list_user_repos(username: str, token: str = None) -> List[Dict[str, Any]]:
    repos = []
    page = 1
    while True:
        url = f"{GITHUB_API_URL}/users/{username}/repos"
        params = {"per_page": 100, "page": page, "sort": "pushed"}
        resp = requests.get(url, headers=_headers(token), params=params, timeout=15)
        _check_rate_limit(resp)
        page_data = resp.json()
        if not page_data:
            break
        repos.extend(page_data)
        if len(page_data) < 100:
            break
        page += 1
    return repos

@disk_cache(namespace="gh_file")
def get_repo_file_content(username: str, repo_name: str, path: str, token: str = None) -> Optional[str]:
    url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/contents/{path}"
    resp = requests.get(url, headers=_headers(token), timeout=5)
    if resp.status_code == 200:
        data = resp.json()
        if isinstance(data, dict) and "content" in data:
            try:
                return base64.b64decode(data["content"]).decode("utf-8", errors="replace")
            except Exception:
                pass
    return None

@disk_cache(namespace="gh_commits")
def get_repo_commits(username: str, repo_name: str, author: str = None, token: str = None, limit: int = 5) -> List[Dict[str, Any]]:
    url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/commits"
    params = {"per_page": limit}
    if author:
        params["author"] = author
    resp = requests.get(url, headers=_headers(token), params=params, timeout=5)
    if resp.status_code == 200:
        return resp.json()
    return []

@disk_cache(namespace="gh_languages")
def get_repo_languages(username: str, repo_name: str, token: str = None) -> Dict[str, int]:
    url = f"{GITHUB_API_URL}/repos/{username}/{repo_name}/languages"
    resp = requests.get(url, headers=_headers(token), timeout=5)
    if resp.status_code == 200:
        return resp.json()
    return {}

@disk_cache(namespace="gh_prs")
def get_user_merged_prs(username: str, token: str = None) -> List[Dict[str, Any]]:
    url = f"{GITHUB_API_URL}/search/issues"
    # Search for merged PRs authored by the user, excluding their own repositories
    params = {
        "q": f"type:pr author:{username} is:merged -user:{username}",
        "per_page": 5,
        "sort": "updated"
    }
    resp = requests.get(url, headers=_headers(token), params=params, timeout=10)
    if resp.status_code == 200:
        return resp.json().get("items", [])
    return []
