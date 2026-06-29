from pydantic import BaseModel, Field
from typing import List

class JobDescriptionProfile(BaseModel):
    role: str = ""
    domain: str = ""
    responsibilities: List[str] = []
    required_skills: List[str] = []
    preferred_skills: List[str] = []
    programming_languages: List[str] = []
    technologies: List[str] = []
    tools: List[str] = []
    frameworks: List[str] = []
    libraries: List[str] = []
    methodologies: List[str] = []
    certifications: List[str] = []
    soft_skills: List[str] = []
    experience: str = ""
    education: str = ""
    industry: str = ""
    keywords: List[str] = []
    ats_keywords: List[str] = []
