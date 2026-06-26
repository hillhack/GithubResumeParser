from services.llm_service import call_llm
from utils.parser import extract_json_from_llm
from utils.github_api import get_user_merged_prs
from typing import List

def extract_oss_contributions(username: str, token: str = None, model_choice: str = "Groq") -> List[dict]:
    """Extracts professional open-source contribution summaries from merged PRs authored by the user in other repositories."""
    
    prs = get_user_merged_prs(username, token)
    if not prs:
        return []
        
    contributions = []
    
    for pr in prs[:3]: # Take top 3 recent PRs
        repo_url = pr.get("repository_url", "").replace("api.github.com/repos/", "github.com/")
        repo_name = repo_url.split("github.com/")[-1] if "github.com/" in repo_url else "Unknown Repository"
        title = pr.get("title", "")
        body = pr.get("body", "") or "No description provided."
        html_url = pr.get("html_url", "")
        
        prompt = f"""Analyze this merged Pull Request from an open-source repository to summarize the contribution for a resume.
Repository: {repo_name}
PR Title: {title}
PR Body:
{body[:2000]}

Return a JSON object:
{{
    "project": "{repo_name}",
    "url": "{html_url}",
    "contribution": "<A 2-3 line resume-ready bullet summarizing the technical impact and technologies used. Use action verbs.>"
}}
"""
        raw = call_llm("You are an expert technical resume writer. Output ONLY JSON.", prompt, model_choice)
        parsed = extract_json_from_llm(raw)
        
        if parsed and "contribution" in parsed:
            contributions.append({
                "project": parsed.get("project", repo_name),
                "url": parsed.get("url", html_url),
                "contribution": parsed.get("contribution")
            })
            
    return contributions
