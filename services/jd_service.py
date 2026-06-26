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
"""
    
    sys_prompt = "You are an expert technical recruiter and requirements analyst. Extract the core requirements accurately. Output ONLY valid JSON."
    
    raw = call_llm(sys_prompt, prompt, model_choice=model_choice)
    parsed = extract_json_from_llm(raw)
    
    safe_parsed = {k: (str(v) if isinstance(v, bool) else v) for k, v in parsed.items()}
    return JobDescriptionProfile(**safe_parsed)
