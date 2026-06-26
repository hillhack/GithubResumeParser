from server import extract_github_metadata, build_repository_profiles, analyze_jd, match_repositories, generate_resume, extract_oss

class ResumeMCPClient:
    def __init__(self):
        pass

    def call(self, tool_name: str, payload: dict) -> dict:
        if tool_name == "extract_github_metadata":
            return extract_github_metadata(
                payload.get("username"),
                payload.get("github_token")
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
                payload.get("profile_dict", {}),
                payload.get("selected_repo_profiles", []),
                payload.get("jd_profile_dict", {}),
                payload.get("user_instructions", ""),
                payload.get("model_choice", "Groq"),
                payload.get("oss_contributions", [])
            )
            
        raise ValueError(f"Unsupported tool: {tool_name}")
