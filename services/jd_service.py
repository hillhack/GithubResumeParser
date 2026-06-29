from models.job_description import JobDescriptionProfile
from services.llm_service import call_llm
from utils.parser import extract_json_from_llm


def analyze_job_description(jd_text: str, model_choice: str = "Groq") -> JobDescriptionProfile:
    """Extracts structured knowledge from a Job Description using an LLM.
    
    Covers all fields required by the pipeline spec: role, domain,
    responsibilities, technologies, tools, frameworks, libraries, languages,
    methodologies, certifications, and ATS keywords.
    """

    prompt = f"""Analyze the following Job Description and extract ONLY concrete, verifiable requirements.

Job Description:
{jd_text[:8000]}

Return a JSON object exactly matching this structure. Do NOT use markdown formatting inside strings:
{{
    "role": "<Job title or position>",
    "domain": "<Primary domain or area of work, e.g. Machine Learning, Full Stack Web Development, DevOps>",
    "responsibilities": ["<key responsibility 1>", "<key responsibility 2>"],
    "required_skills": ["<concrete required skill>"],
    "preferred_skills": ["<concrete preferred skill>"],
    "programming_languages": ["<language 1>", "<language 2>"],
    "technologies": ["<unified list of ALL specific technologies: cloud platforms, databases, APIs, software>"],
    "tools": ["<specific tool, platform or utility, e.g. Docker, Kubernetes, Git, VS Code>"],
    "frameworks": ["<named framework, e.g. PyTorch, TensorFlow, React, FastAPI, Django>"],
    "libraries": ["<specific library/package, e.g. NumPy, Pandas, OpenCV, LangChain>"],
    "methodologies": ["<methodology, standard or protocol, e.g. CI/CD, Agile, REST, GraphQL>"],
    "certifications": ["<certification or qualification if explicitly mentioned>"],
    "experience": "<experience requirement as a string, e.g. 3+ years>",
    "education": "<education requirement>",
    "industry": "<industry sector>",
    "keywords": ["<core technical keyword>"],
    "ats_keywords": ["<ATS-optimised keyword for job matching>"]
}}

EXTRACTION RULES:
1. `required_skills` / `preferred_skills`: Programming languages (Python, Go), cloud platforms (AWS, GCP), databases (PostgreSQL), ML techniques (CNN, LLMs, NLP), or engineering practices (AST parsing, CI/CD).
2. `programming_languages`: Extract only explicit programming/scripting languages (Python, JavaScript, SQL, Bash, etc.).
3. `technologies`: Unified flat list of ALL specific technologies not captured elsewhere — cloud services, databases, APIs, platforms, software applications.
4. `tools`: Named developer tools and utilities (Docker, Kubernetes, Git, Terraform, Streamlit).
5. `frameworks`: Named application or ML frameworks (PyTorch, TensorFlow, React, FastAPI, Django, Next.js).
6. `libraries`: Named code libraries or packages (NumPy, Pandas, scikit-learn, OpenCV, LangChain).
7. `methodologies`: Engineering methodologies, protocols or standards (Agile, CI/CD, REST, GraphQL, TDD).
8. `certifications`: Only if explicitly mentioned in the JD (AWS Certified, PMP, etc.).
9. `ats_keywords`: Key technical terms optimised for ATS scanning (MLOps, DevOps, LLMs, RAG, Computer Vision).

CRITICAL RULE:
NEVER extract soft skills, generic traits or vague concepts such as "passion", "collaboration", "communication", "team player", "problem solving", or "opportunity". If a field has no concrete technical items, leave it as an empty list [].
"""

    sys_prompt = (
        "You are an expert technical recruiter and requirements analyst. "
        "Extract core technical requirements accurately. Output ONLY valid JSON."
    )

    raw = call_llm(sys_prompt, prompt, model_choice=model_choice)
    parsed = extract_json_from_llm(raw)

    # Enforce: soft_skills must always be empty — we do not use them in matching
    parsed["soft_skills"] = []

    # Sanitize: convert any boolean True/False values to strings to prevent Pydantic errors
    safe_parsed = {k: (str(v) if isinstance(v, bool) else v) for k, v in parsed.items()}

    return JobDescriptionProfile(**safe_parsed)
