import json
import logging
from typing import List, Dict

from models.candidate import CandidateDashboardData
from models.repository import RepositoryProfile
from models.job_description import JobDescriptionProfile
from models.match_result import MatchResult

from services.github_service import extract_profile_and_repos
from services.extractor_service import extract_repository_files
from services.readme_service import generate_repository_profile
from services.jd_service import analyze_job_description
from services.matcher_service import match_repository_to_jd
from services.ranking_service import rank_matches, compute_overall_skill_gap
from services.resume_service import generate_resume_content
from services.contribution_service import extract_oss_contributions

log = logging.getLogger(__name__)

def extract_github_metadata(username: str, token: str = None) -> dict:
    """Step 1: Extract basic profile and lightweight repository metadata."""
    profile, repos = extract_profile_and_repos(username, token)
    
    # Just simple stats for the CandidateDashboardData
    langs = {}
    top_repos = []
    
    for r in sorted(repos, key=lambda x: x.metadata.stars, reverse=True):
        top_repos.append(r.metadata.name)
        if r.metadata.default_language:
            langs[r.metadata.default_language] = langs.get(r.metadata.default_language, 0) + 1
            
    dashboard = CandidateDashboardData(
        profile=profile,
        top_technologies=[],
        repository_categories={},
        most_used_languages=langs,
        open_source_contributions=[],
        top_repositories=top_repos[:15]
    )
    
    # We serialize the full repos list so the frontend can keep it in session state
    return {
        "dashboard": dashboard.model_dump(),
        "raw_repos": [r.model_dump() for r in repos]
    }

def build_repository_profiles(username: str, raw_repos: list, selected_repo_names: list, model_choice: str = "Groq", token: str = None) -> list:
    """Step 2: Fully extracts knowledge for selected repositories."""
    from models.repository import Repository
    
    profiles = []
    
    for raw in raw_repos:
        repo = Repository(**raw)
        if repo.metadata.name in selected_repo_names:
            # Deterministic extraction
            repo = extract_repository_files(username, repo, token)
            # LLM Profile extraction
            profile = generate_repository_profile(repo, model_choice)
            profiles.append(profile.model_dump())
            
    return profiles

def analyze_jd(jd_text: str, model_choice: str = "Groq") -> dict:
    """Step 4: Structuring the Job Description."""
    profile = analyze_job_description(jd_text, model_choice)
    return profile.model_dump()

def match_repositories(repo_profiles: list, jd_profile: dict, model_choice: str = "Groq") -> dict:
    """Step 5: Matching."""
    jd = JobDescriptionProfile(**jd_profile)
    
    matches = []
    for raw_prof in repo_profiles:
        repo_prof = RepositoryProfile(**raw_prof)
        match_res = match_repository_to_jd(repo_prof, jd, model_choice)
        matches.append(match_res)
        
    ranked = rank_matches(matches)
    overall_gap = compute_overall_skill_gap(ranked, jd.required_skills + jd.preferred_skills)
    
    return {
        "ranked_matches": [m.model_dump() for m in ranked],
        "overall_skill_gap": overall_gap.model_dump()
    }

def extract_oss(username: str, model_choice: str = "Groq", token: str = None) -> list:
    """Step: Extract OSS Contributions from external merged PRs."""
    return extract_oss_contributions(username, token, model_choice)

def generate_resume(profile_dict: dict, selected_repo_profiles: list, jd_profile_dict: dict, user_instructions: str, model_choice: str = "Groq", oss_contributions: list = None) -> dict:
    """Step 9: Generate final resume."""
    from models.candidate import CandidateProfile
    
    cand = CandidateProfile(**profile_dict)
    repos = [RepositoryProfile(**r) for r in selected_repo_profiles]
    jd = JobDescriptionProfile(**jd_profile_dict)
    
    resume = generate_resume_content(cand, repos, jd, user_instructions, model_choice)
    if oss_contributions:
        resume["contributions"] = oss_contributions
    return resume
