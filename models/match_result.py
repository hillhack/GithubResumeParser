from pydantic import BaseModel, Field, model_validator
from typing import List, Dict, Any

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

    @model_validator(mode="before")
    @classmethod
    def sanitize_lists(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for k, v in data.items():
                if isinstance(v, str) and k in [
                    "matched_skills", "missing_skills", "matched_libraries",
                    "matched_frameworks", "matched_keywords"
                ]:
                    if v.lower() in ["n/a", "none", "null", "", "false"]:
                        data[k] = []
                    else:
                        data[k] = [v]
        return data
    evidence: Dict[str, str] = {} # Key: skill/entity, Value: Reason
    confidence: str = ""

class OverallSkillGap(BaseModel):
    matched_skills: List[str] = []
    missing_skills: List[SkillMatch] = []
    related_skills: List[str] = []
    suggested_projects: List[str] = []
