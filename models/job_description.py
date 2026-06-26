from pydantic import BaseModel, Field
from typing import List

class JobDescriptionProfile(BaseModel):
    role: str = ""
    domain: str = ""
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    tools: List[str] = []
    frameworks: List[str] = []
    libraries: List[str] = []
    soft_skills: List[str] = []
    experience: str = ""
    education: str = ""
    industry: str = ""
    keywords: List[str] = []
    responsibilities: List[str] = []
