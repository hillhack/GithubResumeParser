from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Optional, Any

class CandidateProfile(BaseModel):
    username: str
    name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    website: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    followers: int = 0
    following: int = 0
    public_repos: int = 0
    github_url: str = ""
    linkedin_url: str = ""
    twitter_url: str = ""
    organizations: List[str] = []
    
    # Analyzed fields
    primary_domains: List[str] = []
    programming_languages: List[str] = []
    frameworks: List[str] = []
    tools_and_platforms: List[str] = []
    databases: List[str] = []
    cloud_technologies: List[str] = []
    ai_ml_technologies: List[str] = []
    other_skills: List[str] = []

    @model_validator(mode="before")
    @classmethod
    def sanitize_lists(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str) and k in [
                    "primary_domains", "programming_languages", "frameworks",
                    "tools_and_platforms", "databases", "cloud_technologies",
                    "ai_ml_technologies", "other_skills", "organizations"
                ]:
                    if v.lower() in ["n/a", "none", "null", "", "false"]:
                        data[k] = []
                    else:
                        data[k] = [v]
        return data
    
class CandidateDashboardData(BaseModel):
    profile: CandidateProfile
    top_technologies: List[str] = []
    repository_categories: Dict[str, int] = {}
    most_used_languages: Dict[str, int] = {}
    open_source_contributions: List[dict] = []
    top_repositories: List[str] = []
