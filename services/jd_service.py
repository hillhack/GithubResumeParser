from models.job_description import JobDescriptionProfile
from services.llm_service import call_llm
from utils.parser import extract_json_from_llm

def analyze_job_description(jd_text: str, model_choice: str = "Groq") -> JobDescriptionProfile:
    """Extracts structured knowledge from a Job Description."""
    
    prompt = f"""Analyze the following Job Description and extract structured knowledge.

Job Description:
{jd_text[:8000]}

Return a JSON object exactly matching this structure (do not use markdown formatting in strings):
{{
    "role": "...",
    "domain": "...",
    "required_skills": ["..."],
    "preferred_skills": ["..."],
    "tools": ["..."],
    "frameworks": ["..."],
    "libraries": ["..."],
    "soft_skills": ["..."],
    "experience": "...",
    "education": "...",
    "industry": "...",
    "keywords": ["..."],
    "responsibilities": ["..."]
}}

CRITICAL RULES:
1. ONLY extract hard technical skills (programming languages, frameworks, cloud services, databases, specific ML algorithms, etc.) for `required_skills` and `preferred_skills`.
2. DO NOT include ANY soft skills, personality traits, or vague behavioral abilities (e.g., "curiosity", "problem-solving", "analytical thinking", "passion for learning", "ability to investigate") in `required_skills` or `preferred_skills`. Put those EXCLUSIVELY in `soft_skills`.
"""
    
    sys_prompt = "You are an expert technical recruiter and requirements analyst. Extract the core requirements accurately. Output ONLY valid JSON."
    
    raw = call_llm(sys_prompt, prompt, model_choice=model_choice)
    parsed = extract_json_from_llm(raw)
    
    safe_parsed = {k: (str(v) if isinstance(v, bool) else v) for k, v in parsed.items()}
    return JobDescriptionProfile(**safe_parsed)
