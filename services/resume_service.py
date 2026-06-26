from models.candidate import CandidateProfile
from models.repository import RepositoryProfile
from models.job_description import JobDescriptionProfile
from services.llm_service import call_llm
from utils.parser import extract_json_from_llm
import json

def generate_resume_content(
    profile: CandidateProfile,
    selected_repos: list[RepositoryProfile],
    jd_profile: JobDescriptionProfile,
    user_instructions: str = "",
    model_choice: str = "Groq"
) -> dict:
    """Generates resume bullets using the structured Repository Profiles."""
    
    projects = []
    
    for repo in selected_repos:
        sys_override = f"\n\nCRITICAL USER INSTRUCTIONS:\n{user_instructions}" if user_instructions else ""
        
        prompt = f"""Write resume bullet points for this GitHub project.
Target Role: {jd_profile.role}
Domain: {jd_profile.domain}

Candidate Project Profile:
{repo.model_dump_json()}

Write 3-4 professional, impact-driven action-verb sentences for a resume. Highlight the skills and technologies that match the target role.
CRITICAL: You MUST NOT invent, fabricate, or add any technologies, skills, or features that are not explicitly present in the Candidate Project Profile. Rely ONLY on the provided profile.
Also provide a 1-sentence one_liner.

Return ONLY JSON:
{{
    "bullets": ["<bullet 1>", "<bullet 2>", "<bullet 3>"],
    "tech_stack": ["<tech1>", "<tech2>"],
    "one_liner": "<one sentence>"
}}
"""
        raw = call_llm(f"You are an expert resume writer. Output ONLY JSON.{sys_override}", prompt, model_choice)
        parsed = extract_json_from_llm(raw)
        
        projects.append({
            "name": repo.name,
            "url": f"https://github.com/{profile.username}/{repo.name}",
            "bullets": parsed.get("bullets", [f"Built {repo.name}."]),
            "tech_stack": parsed.get("tech_stack", repo.primary_skills + repo.frameworks),
            "one_liner": parsed.get("one_liner", repo.one_line_summary)
        })

    # Generate Professional Summary
    sum_prompt = f"""Write a 2-3 sentence professional summary for a resume.
Candidate: {profile.name or profile.username}
Role: {jd_profile.role}
Top Projects: {[p['name'] for p in projects]}

Return JSON: {{"summary": "<2-3 sentences>"}}"""
    
    raw = call_llm("Return ONLY JSON.", sum_prompt, model_choice)
    summary = extract_json_from_llm(raw).get("summary", "")

    # Aggregate skills
    all_skills = set()
    for repo in selected_repos:
        all_skills.update(repo.primary_skills)
        all_skills.update(repo.frameworks)
        all_skills.update(repo.libraries)
        all_skills.update(repo.tools)
        all_skills.update(repo.programming_languages)

    return {
        "profile": {
            "username": profile.username,
            "name": profile.name or profile.username,
            "email": profile.email,
            "location": profile.location,
            "html_url": f"https://github.com/{profile.username}",
            "blog": profile.website,
            "summary": profile.bio,
        },
        "summary": summary,
        "pages": 1,
        "projects": projects,
        "skills_section": {
            "Core Technologies": list(all_skills)[:20]
        },
        "contributions": [],
        "jd_analysis": jd_profile.model_dump()
    }
