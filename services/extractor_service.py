"""extractor_service.py — Deterministic repository file extraction.

Fetches important files from GitHub, parses them for technology signals,
and normalizes all detected technologies. No LLM is used here.
"""

from models.repository import Repository
from utils.constants import IMPORTANT_FILES
from utils.github_api import get_repo_file_content, get_repo_languages, get_repo_commits
from utils.dependency_parser import parse_all_files
from utils.technology_normalizer import normalize_list
from concurrent.futures import ThreadPoolExecutor


def extract_repository_files(username: str, repo: Repository, token: str = None) -> Repository:
    """Deterministically extract files, languages, commits, and technologies for a repository."""

    # 1. Languages and recent commits
    languages = get_repo_languages(username, repo.metadata.name, token)
    repo.metadata.languages = languages

    # Commits on personal repos are a waste of time (usually trivial), so we no longer fetch them here.

    # 2. Fetch all important files concurrently
    def fetch_file(file_path: str):
        content = get_repo_file_content(username, repo.metadata.name, file_path, token)
        return file_path, content

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = list(executor.map(fetch_file, IMPORTANT_FILES))

    # 3. Populate repo files
    raw_file_contents: dict[str, str] = {}
    for file_path, content in results:
        if not content:
            continue
        filename_lower = file_path.lower().split("/")[-1]
        if filename_lower == "readme.md":
            repo.files.readme = content[:15000]
        else:
            repo.files.detected_files.append(file_path)
            repo.files.file_contents[file_path] = content[:5000]
            raw_file_contents[file_path] = content

    # 4. Deterministic technology extraction — parse all dependency files
    raw_techs = parse_all_files(raw_file_contents)

    # Also add GitHub topics and primary language as signals
    raw_techs.extend(repo.metadata.topics)
    if repo.metadata.default_language:
        raw_techs.append(repo.metadata.default_language)
    raw_techs.extend(repo.metadata.languages.keys())

    # 5. Normalize — deduplicate and apply canonical names
    repo.files.detected_technologies = normalize_list(raw_techs)

    return repo
