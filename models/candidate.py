from pydantic import BaseModel, Field
from typing import List, Dict, Optional

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
    
class CandidateDashboardData(BaseModel):
    profile: CandidateProfile
    top_technologies: List[str] = []
    repository_categories: Dict[str, int] = {}
    most_used_languages: Dict[str, int] = {}
    open_source_contributions: List[dict] = []
    top_repositories: List[str] = []
