from models.match_result import MatchResult, OverallSkillGap, SkillMatch
from typing import List, Dict

def rank_matches(match_results: List[MatchResult]) -> List[MatchResult]:
    """Ranks repository matches by their overall score."""
    return sorted(match_results, key=lambda x: x.overall_score, reverse=True)

def compute_overall_skill_gap(match_results: List[MatchResult], jd_required_skills: List[str]) -> OverallSkillGap:
    """Computes the overall skill gap across all analyzed repositories."""
    
    all_matched_skills = set()
    evidence_map = {}
    
    for match in match_results:
        all_matched = match.matched_skills + match.matched_tools + match.matched_frameworks + match.matched_libraries + match.matched_keywords
        for skill in all_matched:
            all_matched_skills.add(skill)
            if skill not in evidence_map and skill in match.evidence:
                evidence_map[skill] = match.evidence[skill]
                
    missing = []
    
    # Case-insensitive comparison for matching
    matched_skills_lower = {s.lower() for s in all_matched_skills}
    
    # Standardize cased matched skills based on the Job Description's casing
    matched = []
    for skill in jd_required_skills:
        if skill.lower() in matched_skills_lower:
            matched.append(skill)
            
    for skill in jd_required_skills:
        if skill.lower() not in matched_skills_lower:
            missing.append(SkillMatch(
                skill=skill,
                is_matched=False,
                priority="High",
                recommendation=f"Consider adding a project that uses {skill}."
            ))
            
    return OverallSkillGap(
        matched_skills=matched,
        missing_skills=missing,
        related_skills=[],
        suggested_projects=[m.recommendation for m in missing]
    )
