from models.candidate import CandidateProfile
from models.repository import Repository, RepositoryMetadata, RepositoryFiles
from utils.github_api import get_user, list_user_repos
from typing import List, Tuple

def extract_profile_and_repos(username: str, token: str = None) -> Tuple[CandidateProfile, List[Repository]]:
    user_data = get_user(username, token)
    
    profile = CandidateProfile(
        username=user_data.get("login", username),
        name=user_data.get("name"),
        bio=user_data.get("bio"),
        location=user_data.get("location"),
        website=user_data.get("blog"),
        email=user_data.get("email"),
        avatar=user_data.get("avatar_url"),
        followers=user_data.get("followers", 0),
        following=user_data.get("following", 0),
        public_repos=user_data.get("public_repos", 0)
    )
    
    repos_data = list_user_repos(username, token)
    repos = []
    for r in repos_data:
        if r.get("size", 0) == 0 or r.get("fork", False):
            continue
            
        metadata = RepositoryMetadata(
            name=r["name"],
            description=r.get("description"),
            url=r.get("html_url", ""),
            stars=r.get("stargazers_count", 0),
            forks=r.get("forks_count", 0),
            topics=r.get("topics", []),
            default_language=r.get("language"),
            license=r.get("license", {}).get("name") if r.get("license") else None,
            created_date=r.get("created_at"),
            updated_date=r.get("updated_at"),
            archived=r.get("archived", False),
            is_fork=r.get("fork", False)
        )
        
        repo = Repository(
            metadata=metadata,
            files=RepositoryFiles()
        )
        repos.append(repo)
        
    return profile, repos
