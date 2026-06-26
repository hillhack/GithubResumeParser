from models.repository import Repository
from utils.constants import IMPORTANT_FILES
from utils.github_api import get_repo_file_content, get_repo_languages, get_repo_commits
from concurrent.futures import ThreadPoolExecutor

def extract_repository_files(username: str, repo: Repository, token: str = None) -> Repository:
    """Deterministically extracts important files for a repository."""
    
    # 1. Languages and Commits
    languages = get_repo_languages(username, repo.metadata.name, token)
    repo.metadata.languages = languages
    
    commits = get_repo_commits(username, repo.metadata.name, author=username, token=token, limit=5)
    repo.metadata.user_commits = [c.get("commit", {}).get("message", "").split("\n")[0] for c in commits if isinstance(c, dict)]
    
    # 2. Check for important files
    # We can do this concurrently to save time
    
    def fetch_file(file_path):
        content = get_repo_file_content(username, repo.metadata.name, file_path, token)
        return file_path, content

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = executor.map(fetch_file, IMPORTANT_FILES)
        
    for file_path, content in results:
        if content:
            # Special case README
            if file_path.lower() == "readme.md":
                repo.files.readme = content[:15000] # Truncate massive readmes
            else:
                repo.files.detected_files.append(file_path)
                # Store contents for package files up to a limit
                repo.files.file_contents[file_path] = content[:5000]
                
    return repo
