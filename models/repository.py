from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class RepositoryMetadata(BaseModel):
    name: str
    description: Optional[str] = None
    url: str
    stars: int = 0
    forks: int = 0
    topics: List[str] = []
    default_language: Optional[str] = None
    languages: Dict[str, int] = {}
    license: Optional[str] = None
    created_date: Optional[str] = None
    updated_date: Optional[str] = None
    archived: bool = False
    is_fork: bool = False
    user_commits: List[str] = []

class RepositoryFiles(BaseModel):
    readme: Optional[str] = None
    detected_files: List[str] = []
    file_contents: Dict[str, str] = {} # e.g. requirements.txt contents if needed
    
class RepositoryProfile(BaseModel):
    name: str
    one_line_summary: str = ""
    project_purpose: str = ""
    problem_solved: str = ""
    target_users: str = ""
    project_type: str = ""
    domain: str = ""
    key_features: List[str] = []
    architecture_patterns: List[str] = []
    primary_skills: List[str] = []
    secondary_skills: List[str] = []
    frameworks: List[str] = []
    libraries: List[str] = []
    tools: List[str] = []
    programming_languages: List[str] = []
    deployment: List[str] = []
    database: List[str] = []
    cloud: List[str] = []
    ai_models: List[str] = []
    apis: List[str] = []
    visualization: List[str] = []
    research_area: str = ""
    keywords: List[str] = []
    tags: List[str] = []
    evidence_summary: str = ""

class Repository(BaseModel):
    metadata: RepositoryMetadata
    files: RepositoryFiles
    profile: Optional[RepositoryProfile] = None
