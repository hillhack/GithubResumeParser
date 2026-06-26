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
        for skill in match.matched_skills:
            all_matched_skills.add(skill)
            if skill not in evidence_map and skill in match.evidence:
                evidence_map[skill] = match.evidence[skill]
                
    missing = []
    matched = list(all_matched_skills)
    
    for skill in jd_required_skills:
        if skill not in all_matched_skills:
            # We can expand this to use LLM to find related skills or recommend projects
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
