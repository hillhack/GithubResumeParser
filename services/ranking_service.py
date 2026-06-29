from models.match_result import MatchResult, OverallSkillGap, SkillMatch
from typing import List, Dict

def rank_matches(match_results: List[MatchResult]) -> List[MatchResult]:
    """Ranks repository matches by their overall score."""
    return sorted(match_results, key=lambda x: x.overall_score, reverse=True)

from services.matcher_service import skill_matches_jd

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
    matched = []
    
    # Deduplicate jd skills that mean the exact same thing (e.g. AI and Artificial Intelligence)
    deduped_jd_skills = []
    for skill in jd_required_skills:
        # Check if this skill is already represented by a synonym in deduped_jd_skills
        if not any(skill_matches_jd(skill, [existing]) for existing in deduped_jd_skills):
            deduped_jd_skills.append(skill)
            
    # Now check if each unique JD skill is matched by the candidate's repos
    for skill in deduped_jd_skills:
        is_matched = any(skill_matches_jd(skill, [m]) for m in all_matched_skills)
        if is_matched:
            matched.append(skill)
        else:
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
