import os
import contextvars
from typing import Dict, List, Any
from fastmcp import FastMCP
from tools import extract_jd_skills_tool, analyse_repos_tool, generate_resume_tool

# Initialize the MCP server
mcp = FastMCP("AllDone Agent Server")

@mcp.tool()
def extract_jd_skills(jd_text: str, provider: str = "Groq", model: str = "llama-3.3-70b-versatile") -> Dict:
    """
    Extracts atomic technical skills, domains, and tools from a Job Description text.
    
    Args:
        jd_text: Raw job description text.
        provider: LLM provider ("Groq", "Gemini", "HuggingFace").
        model: Specific model name for the provider.
        
    Returns:
        Structured JSON dictionary of categorized skills.
    """
    return extract_jd_skills_tool(jd_text, provider, model)

@mcp.tool()
def analyse_repos(repos: List[Dict[str, Any]], jd_data: Dict, github_username: str, provider: str = "Groq", model: str = "llama-3.3-70b-versatile") -> List[Dict]:
    """
    Hybrid two-pass repository analyser. Computes deterministic keyword overlap and LLM semantic relevance.
    
    Args:
        repos: Selected repo dicts (each must have 'name', 'url', 'description').
        jd_data: Extracted JD skills dict from extract_jd_skills.
        github_username: GitHub username (needed for API calls).
        provider: LLM provider ("Groq", "Gemini", "HuggingFace").
        model: Specific model name for the provider.
        
    Returns:
        List of result dicts sorted by match_score descending.
    """
    return analyse_repos_tool(repos, jd_data, github_username, provider, model)

@mcp.tool()
def generate_resume(github_username: str, match_results: List[Dict], jd_data: Dict, instructions: str = "", provider: str = "Groq", model: str = "llama-3.3-70b-versatile") -> Dict:
    """
    Generates a professional ATS Resume based strictly on verified GitHub work.
    
    Args:
        github_username: GitHub username.
        match_results: Ranked match results from analyse_repos.
        jd_data: Extracted JD skills dict.
        instructions: Custom instructions for the resume generation.
        provider: LLM provider ("Groq", "Gemini", "HuggingFace").
        model: Specific model name for the provider.
        
    Returns:
        Structured JSON dictionary matching the resume schema.
    """
    return generate_resume_tool(github_username, match_results, jd_data, instructions, provider, model)

if __name__ == "__main__":
    # Ensure keys are available in the environment if running as an agent server
    mcp.run()
