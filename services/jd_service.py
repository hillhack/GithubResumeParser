from models.job_description import JobDescriptionProfile
from services.llm_service import call_llm
from utils.parser import extract_json_from_llm

def analyze_job_description(jd_text: str, model_choice: str = "Groq") -> JobDescriptionProfile:
    """Extracts structured knowledge from a Job Description."""
    
    prompt = f"""Analyze the following Job Description and extract ONLY concrete technical requirements.

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
    "soft_skills": [],
    "experience": "...",
    "education": "...",
    "industry": "...",
    "keywords": ["..."],
    "responsibilities": ["..."]
}}

SPECIFIC EXTRACTION TARGETS:
1. `required_skills` / `preferred_skills`: Extract ONLY concrete programming languages (e.g., Python, C++, Go), cloud platforms (e.g., AWS, GCP), databases (e.g., PostgreSQL, MongoDB), specific machine learning/AI techniques or architectures (e.g., CNN, Transformers, LLMs, NLP, CV), or core engineering practices (e.g., AST parsing, CI/CD).
2. `tools`: Extract ONLY specific software tools, development platforms, or developer utilities (e.g., Docker, Kubernetes, Git, VS Code, Streamlit).
3. `frameworks`: Extract ONLY named application or machine learning frameworks (e.g., PyTorch, TensorFlow, React, Next.js, FastAPI, Flask, Django).
4. `libraries`: Extract ONLY specific code libraries/packages (e.g., NumPy, Pandas, scikit-learn, OpenCV, LangChain, rasterio, torchvision).
5. `keywords`: Extract ONLY core technical industry keywords (e.g., MLOps, DevOps, AST, Model Context Protocol).

CRITICAL RULE:
Do NOT extract any general/generic concepts, qualities, or traits. Specifically, NEVER extract items like "passion", "collaboration", "communication", "collaborative environment", "projects", "real-world projects", "hands-on experience", "team player", "problem-solving", or "opportunity". If a field has no concrete technical items matching the targets above, leave it as an empty list `[]`.
"""
    
    sys_prompt = "You are an expert technical recruiter and requirements analyst. Extract the core requirements accurately. Output ONLY valid JSON."
    
    raw = call_llm(sys_prompt, prompt, model_choice=model_choice)
    parsed = extract_json_from_llm(raw)
    
    # Force soft_skills to remain empty as we focus purely on technical matching
    parsed["soft_skills"] = []
    
    safe_parsed = {k: (str(v) if isinstance(v, bool) else v) for k, v in parsed.items()}
    return JobDescriptionProfile(**safe_parsed)
