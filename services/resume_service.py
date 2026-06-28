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
    match_results: list[dict] = None,
    user_instructions: str = "",
    model_choice: str = "Groq"
) -> dict:
    """Generates resume bullets using the structured Repository Profiles."""
    
    projects = []
    
    for repo in selected_repos:
        sys_override = f"\n\nCRITICAL USER INSTRUCTIONS:\n{user_instructions}" if user_instructions else ""
        
        # Find matching MatchResult if available
        repo_match_info = ""
        if match_results:
            for mr in match_results:
                if mr.get("repository_name") == repo.name:
                    repo_match_info = f"\nSkills this repo successfully matched from JD:\n{', '.join(mr.get('matched_skills', []))}\nEvidence: {json.dumps(mr.get('evidence', {}))}\n"
                    break
        
        prompt = f"""Write resume bullet points for this GitHub project.
Target Role: {jd_profile.role}
Domain: {jd_profile.domain}

Job Description Required Skills: {', '.join(jd_profile.required_skills)}
Job Description Preferred Skills: {', '.join(jd_profile.preferred_skills)}
{repo_match_info}
Candidate Project Profile:
{repo.model_dump_json()}

Follow these strict rules:
1. Write exactly 3 highly professional, extremely concise, punchy bullet points (maximum 15-20 words per bullet; not 4, exactly 3). Start each bullet point with a strong action verb, describing HOW you solved the problem (specific features, engineering choices) in a direct, to-the-point manner. Ensure you highlight the matched skills and evidence provided.
2. Provide a single, complete, well-formed sentence (about 15-25 words, spanning a full line) describing the project's core purpose, the specific problem it solves, and the high-level architecture.
3. Filter the tech stack to ONLY include technologies relevant to the Job Description skills above, plus 1 or 2 core defining technologies of the project. Keep the total tech stack list to 5-8 items maximum.
CRITICAL: Explicitly incorporate the 'domain', 'key_features', and 'architecture_patterns' into your bullet points, but keep them extremely brief and to the point. Do not make up info.

Return ONLY JSON:
{{
    "bullets": ["<bullet 1>", "<bullet 2>", "<bullet 3>"],
    "tech_stack": ["<tech1>", "<tech2>"],
    "one_liner": "<one complete sentence explaining the core purpose and architecture>"
}}
"""
        raw = call_llm(f"You are an expert resume writer. Output ONLY JSON.{sys_override}", prompt, model_choice)
        parsed = extract_json_from_llm(raw)
        
        projects.append({
            "name": repo.name,
            "url": f"https://github.com/{profile.username}/{repo.name}",
            "bullets": parsed.get("bullets", [f"Built {repo.name}."])[:3],
            "tech_stack": parsed.get("tech_stack", repo.primary_skills + repo.frameworks),
            "one_liner": parsed.get("one_liner", repo.one_line_summary)
        })

    # Generate Professional Summary
    sum_prompt = f"""Write a highly concise (max 2-3 lines) ATS-friendly professional summary.
CRITICAL: The summary MUST directly connect the candidate's specific top projects and technical skills to the core requirements of the Job Description. Do NOT use fluff words (e.g. passionate, motivated). Only state factual overlaps between what they have built and what the JD needs.

Candidate: {profile.name or profile.username}
Bio: {profile.bio}
Domains: {profile.primary_domains}
Job Role: {jd_profile.role}
Required JD Skills: {', '.join(jd_profile.required_skills)}
Top Candidate Projects: {[p['name'] for p in projects]}

Return ONLY JSON: {{"summary": "<2-3 sentence tailored summary>"}}"""
    
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
        
    skills_dict = {}
    
    # Aggregate all skills cleanly from Profile and Repositories
    lang_set = set(profile.programming_languages or [])
    frameworks_set = set(profile.frameworks or [])
    tools_set = set(profile.tools_and_platforms or [])
    db_cloud_set = set((profile.databases or []) + (profile.cloud_technologies or []))
    
    for repo in selected_repos:
        lang_set.update(repo.programming_languages or [])
        frameworks_set.update((repo.frameworks or []) + (repo.libraries or []))
        tools_set.update(repo.tools or [])
        db_cloud_set.update((repo.database or []) + (repo.cloud or []))
        
    skills_dict = {}
    if lang_set:
        skills_dict["Languages"] = list(lang_set)
    if frameworks_set:
        skills_dict["Frameworks & Libraries"] = list(frameworks_set)
    if tools_set:
        skills_dict["Tools & Platforms"] = list(tools_set)
    if db_cloud_set:
        skills_dict["Databases & Cloud"] = list(db_cloud_set)

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
