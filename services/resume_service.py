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

Follow these strict rules:
1. Write exactly 3-4 concise bullets focusing on what was built, tech used, problem solved, and measurable impact.
2. Provide a 1-sentence one_liner (max 20-30 words) explaining what the project does. Do not repeat the same info from bullets.
3. Extract the tech stack (languages, frameworks, DBs, cloud, APIs).
CRITICAL: You MUST NOT invent, fabricate, or add any technologies, skills, or features that are not explicitly present in the Candidate Project Profile.

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
    sum_prompt = f"""Write a concise (3-4 lines) ATS-friendly professional summary.
Avoid generic statements (Highly motivated, Passionate). Describe experience areas, technical strengths, system types, and specialization.
Candidate: {profile.name or profile.username}
Bio: {profile.bio}
Domains: {profile.primary_domains}
Role: {jd_profile.role}
Top Projects: {[p['name'] for p in projects]}

Return ONLY JSON: {{"summary": "<3-4 sentences ATS-friendly>"}}"""
    
    raw = call_llm("Return ONLY JSON.", sum_prompt, model_choice)
    summary = extract_json_from_llm(raw).get("summary", "")

    # Extract JD skills
    jd_skills = set(s.lower() for s in jd_profile.required_skills + jd_profile.preferred_skills)
    
    # Extract candidate skills
    candidate_skills = set()
    if profile.programming_languages: candidate_skills.update(profile.programming_languages)
    if profile.frameworks: candidate_skills.update(profile.frameworks)
    if profile.tools_and_platforms: candidate_skills.update(profile.tools_and_platforms)
    if profile.databases: candidate_skills.update(profile.databases)
    if profile.cloud_technologies: candidate_skills.update(profile.cloud_technologies)
    if profile.ai_ml_technologies: candidate_skills.update(profile.ai_ml_technologies)
    if profile.other_skills: candidate_skills.update(profile.other_skills)
    
    for repo in selected_repos:
        candidate_skills.update(repo.primary_skills)
        candidate_skills.update(repo.frameworks)
        candidate_skills.update(repo.libraries)
        candidate_skills.update(repo.tools)
        candidate_skills.update(repo.programming_languages)
        
    # Deterministic matching
    matched_skills = []
    for skill in candidate_skills:
        if skill.lower() in jd_skills:
            matched_skills.append(skill)
            
    # Fallback to top candidate skills if no match
    if not matched_skills:
        matched_skills = list(candidate_skills)[:15]
        
    skills_dict = {"JD Matched Skills": matched_skills}
    
    # Restore Categorized Skills from Profile
    if profile.programming_languages: skills_dict["Languages"] = profile.programming_languages
    if profile.frameworks: skills_dict["Technologies"] = profile.frameworks
    if profile.tools_and_platforms: skills_dict["Tools"] = profile.tools_and_platforms
    if profile.databases: skills_dict["Databases"] = profile.databases
    if profile.cloud_technologies: skills_dict["Cloud"] = profile.cloud_technologies

    return {
        "profile": {
            "username": profile.username,
            "name": profile.name or profile.username,
            "email": profile.email,
            "location": profile.location,
            "github_url": profile.github_url or f"https://github.com/{profile.username}",
            "linkedin_url": profile.linkedin_url,
            "twitter_url": profile.twitter_url,
            "website": profile.website,
            "organizations": profile.organizations,
            "summary": profile.bio,
        },
        "summary": summary,
        "pages": 1,
        "projects": projects,
        "skills_section": skills_dict,
        "contributions": [],
        "jd_analysis": jd_profile.model_dump()
    }
