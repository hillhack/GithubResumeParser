from pydantic import BaseModel, Field
from typing import List, Dict

class SkillMatch(BaseModel):
    skill: str
    is_matched: bool
    evidence: str = ""
    confidence: str = "" # e.g. "High", "Medium", "Low"
    priority: str = "" # e.g. "High", "Low"
    recommendation: str = "" # for missing skills

class MatchResult(BaseModel):
    repository_name: str
    overall_score: float = 0.0 # 0.0 to 1.0
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    matched_libraries: List[str] = []
    matched_frameworks: List[str] = []
    matched_domain: str = ""
    matched_keywords: List[str] = []
    evidence: Dict[str, str] = {} # Key: skill/entity, Value: Reason
    confidence: str = ""

class OverallSkillGap(BaseModel):
    matched_skills: List[str] = []
    missing_skills: List[SkillMatch] = []
    related_skills: List[str] = []
    suggested_projects: List[str] = []
