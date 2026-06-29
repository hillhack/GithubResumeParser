from server import extract_github_metadata, build_repository_profiles, analyze_jd, match_repositories, generate_resume, extract_oss
from utils.keys import api_keys_ctx

class ResumeMCPClient:
    def __init__(self):
        pass

    def call(self, tool_name: str, payload: dict) -> dict:
        import os
        
        # Capture keys securely for this specific thread/request
        request_keys = {}
        request_keys["GROQ_API_KEY"] = payload.get("groq_api_key") or os.environ.get("GROQ_API_KEY")
        request_keys["GEMINI_API_KEY"] = payload.get("gemini_api_key") or os.environ.get("GEMINI_API_KEY")
        request_keys["GITHUB_TOKEN"] = payload.get("github_token") or os.environ.get("GITHUB_TOKEN")
        request_keys["HF_TOKEN"] = payload.get("hf_token") or os.environ.get("HF_TOKEN")
        
        # Set keys in the context variable for downstream providers
        token = api_keys_ctx.set(request_keys)
        
        # Provide fallback values directly in the payload if needed
        payload["github_token"] = request_keys["GITHUB_TOKEN"]
        
        try:
            if tool_name == "extract_github_metadata":
                return extract_github_metadata(
                    payload.get("username"),
                    payload.get("github_token"),
                    payload.get("model_choice", "Groq")
                )
                
            if tool_name == "build_repository_profiles":
                return build_repository_profiles(
                    payload.get("username"),
                    payload.get("raw_repos", []),
                    payload.get("selected_repo_names", []),
                    payload.get("model_choice", "Groq"),
                    payload.get("github_token")
                )
                
            if tool_name == "analyze_jd":
                return analyze_jd(
                    payload.get("jd_text", ""),
                    payload.get("model_choice", "Groq")
                )
                
            if tool_name == "match_repositories":
                return match_repositories(
                    payload.get("repo_profiles", []),
                    payload.get("jd_profile", {}),
                    payload.get("raw_repos", []),
                    payload.get("model_choice", "Groq")
                )
                
            if tool_name == "extract_oss":
                return extract_oss(
                    payload.get("username"),
                    payload.get("model_choice", "Groq"),
                    payload.get("github_token")
                )
                
            if tool_name == "generate_resume":
                return generate_resume(
                    profile_dict=payload.get("profile_dict", {}),
                    selected_repo_profiles=payload.get("selected_repo_profiles", []),
                    jd_profile_dict=payload.get("jd_profile_dict", {}),
                    user_instructions=payload.get("user_instructions", ""),
                    match_results=payload.get("match_results"),
                    model_choice=payload.get("model_choice", "Groq"),
                    oss_contributions=payload.get("oss_contributions", [])
                )
                
            raise ValueError(f"Unsupported tool: {tool_name}")
            
        finally:
            api_keys_ctx.reset(token)
