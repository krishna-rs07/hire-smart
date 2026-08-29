"""
Scoring Engine Module
Implements hybrid scoring: Skills 40% + Semantic 25% + Experience 15% + Education 10% + Preferred 10%.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field

from .skill_extractor import SkillExtractor
from .similarity_engine import SimilarityEngine
from .job_analyzer import JobAnalyzer, JobRequirements

logger = logging.getLogger(__name__)


@dataclass
class ScoreBreakdown:
    """Detailed score breakdown for a candidate-job pair."""
    skill_score: float = 0.0
    semantic_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    preferred_skill_score: float = 0.0
    job_title_score: float = 0.0
    overall_score: float = 0.0

    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    missing_preferred_skills: List[str] = field(default_factory=list)

    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'skill_score': round(self.skill_score, 2),
            'semantic_score': round(self.semantic_score, 2),
            'experience_score': round(self.experience_score, 2),
            'education_score': round(self.education_score, 2),
            'preferred_skill_score': round(self.preferred_skill_score, 2),
            'job_title_score': round(self.job_title_score, 2),
            'overall_score': round(self.overall_score, 2),
            'matched_skills': self.matched_skills,
            'missing_skills': self.missing_skills,
            'missing_preferred_skills': self.missing_preferred_skills,
            'strengths': self.strengths,
            'weaknesses': self.weaknesses
        }


class ScoringEngine:
    """
    Hybrid scoring engine for candidate-job matching.

    Weights:
    - Skills: 40%
    - Semantic similarity: 25%
    - Experience: 15%
    - Education: 10%
    - Preferred skills: 10%
    """

    # Default weights
    DEFAULT_WEIGHTS = {
        'skill': 0.35,
        'semantic': 0.20,
        'experience': 0.15,
        'education': 0.10,
        'preferred': 0.10,
        'job_title': 0.10
    }

    def __init__(self, weights: Optional[Dict[str, float]] = None,
                 skill_extractor: Optional[SkillExtractor] = None,
                 similarity_engine: Optional[SimilarityEngine] = None,
                 job_analyzer: Optional[JobAnalyzer] = None):
        """
        Initialize the scoring engine.

        Args:
            weights: Custom scoring weights (must sum to 1.0)
            skill_extractor: SkillExtractor instance
            similarity_engine: SimilarityEngine instance
            job_analyzer: JobAnalyzer instance
        """
        if weights:
            # Validate weights sum to 1.0
            total = sum(weights.values())
            if abs(total - 1.0) > 0.01:
                logger.warning(f"Weights sum to {total}, not 1.0. Normalizing.")
                weights = {k: v / total for k, v in weights.items()}
            self.weights = weights
        else:
            self.weights = self.DEFAULT_WEIGHTS.copy()

        self.skill_extractor = skill_extractor or SkillExtractor()
        self.similarity_engine = similarity_engine or SimilarityEngine(
            skill_extractor=self.skill_extractor
        )
        self.job_analyzer = job_analyzer or JobAnalyzer(
            skill_extractor=self.skill_extractor
        )

    def score_candidate(self, resume_text: str, job_description: str,
                        job_requirements: Optional[JobRequirements] = None) -> ScoreBreakdown:
        """
        Score a candidate resume against a job.

        Args:
            resume_text: Resume text
            job_description: Job description text
            job_requirements: Pre-analyzed job requirements (optional)

        Returns:
            ScoreBreakdown with detailed scores and explanations
        """
        if not resume_text or not resume_text.strip():
            return ScoreBreakdown()  # All zeros

        # Analyze job requirements if not provided
        if job_requirements is None:
            job_requirements = self.job_analyzer.analyze(job_description)

        # Extract candidate skills
        candidate_skills_result = self.skill_extractor.extract_skills(resume_text)
        candidate_skills = set(candidate_skills_result.get('skills', []))

        # Compute skill score
        skill_score, matched, missing = self._score_skills(
            candidate_skills,
            job_requirements.required_skills
        )

        # Compute preferred skill score
        pref_score, missing_pref = self._score_preferred_skills(
            candidate_skills,
            job_requirements.preferred_skills
        )

        # Compute semantic similarity score
        semantic_score = self.similarity_engine.compute_similarity(
            resume_text, job_description, use_skills=True
        )

        # Compute experience score
        experience_score = self._score_experience(
            resume_text,
            job_requirements.required_experience,
            job_requirements.preferred_experience
        )

        # Compute education score
        education_score = self._score_education(
            resume_text,
            job_requirements.required_education,
            job_requirements.preferred_education
        )

        # Compute job title relevance score
        job_title_score = self._score_job_title(resume_text, job_description)

        # Compute overall weighted score
        overall = (
            self.weights['skill'] * skill_score +
            self.weights['semantic'] * semantic_score +
            self.weights['experience'] * experience_score +
            self.weights['education'] * education_score +
            self.weights['preferred'] * pref_score +
            self.weights['job_title'] * job_title_score
        )

        # Generate explanations
        strengths, weaknesses = self._generate_explanations(
            skill_score, semantic_score, experience_score,
            education_score, pref_score,
            matched, missing, missing_pref,
            job_requirements
        )

        return ScoreBreakdown(
            skill_score=skill_score,
            semantic_score=semantic_score,
            experience_score=experience_score,
            education_score=education_score,
            preferred_skill_score=pref_score,
            job_title_score=job_title_score,
            overall_score=overall,
            matched_skills=matched,
            missing_skills=missing,
            missing_preferred_skills=missing_pref,
            strengths=strengths,
            weaknesses=weaknesses
        )

    def _score_skills(self, candidate_skills: set, required_skills: List[str]) -> Tuple[float, List[str], List[str]]:
        """
        Score candidate against required skills.

        Returns:
            (score 0-100, matched_skills, missing_skills)
        """
        if not required_skills:
            return 100.0, [], []  # No requirements = perfect score

        if not candidate_skills:
            return 0.0, [], list(required_skills)

        matched = [skill for skill in required_skills if skill in candidate_skills]
        missing = [skill for skill in required_skills if skill not in candidate_skills]

        score = (len(matched) / len(required_skills)) * 100

        return score, matched, missing

    def _score_preferred_skills(self, candidate_skills: set, preferred_skills: List[str]) -> Tuple[float, List[str]]:
        """
        Score candidate against preferred skills.

        Returns:
            (score 0-100, missing_preferred_skills)
        """
        if not preferred_skills:
            return 50.0, []  # Neutral score if no preferred skills specified

        if not candidate_skills:
            return 0.0, list(preferred_skills)

        matched_count = sum(1 for skill in preferred_skills if skill in candidate_skills)
        missing = [skill for skill in preferred_skills if skill not in candidate_skills]

        score = (matched_count / len(preferred_skills)) * 100

        return score, missing

    def _score_experience(self, resume_text: str, required_exp: int, preferred_exp: int) -> float:
        """
        Score candidate experience.

        Args:
            resume_text: Resume text
            required_exp: Required years
            preferred_exp: Preferred years

        Returns:
            Score (0-100)
        """
        candidate_exp = self.skill_extractor.extract_experience_years(resume_text)

        if required_exp <= 0:
            # No requirement specified
            if candidate_exp > 0:
                return 100.0
            return 50.0

        if candidate_exp >= required_exp:
            # Meets requirement
            if candidate_exp >= preferred_exp and preferred_exp > 0:
                # Exceeds preferred - cap at 100
                return 100.0
            # Between required and preferred
            if preferred_exp > required_exp:
                ratio = (candidate_exp - required_exp) / (preferred_exp - required_exp)
                return 80 + 20 * min(ratio, 1.0)  # 80-100 range
            return 100.0
        else:
            # Below requirement - proportional score
            ratio = candidate_exp / required_exp
            return max(0.0, ratio * 80)  # Up to 80 if at requirement

    def _score_education(self, resume_text: str, required_edu: List[str], preferred_edu: List[str]) -> float:
        """
        Score candidate education.

        Returns:
            Score (0-100)
        """
        candidate_edu = self.skill_extractor.extract_education(resume_text)

        if not required_edu:
            return 70.0  # Neutral if no requirement

        if not candidate_edu:
            return 0.0

        # Extract degree levels from required and candidate education
        required_levels = self._extract_degree_levels(required_edu)
        candidate_levels = self._extract_degree_levels(candidate_edu)
        required_fields = self._extract_education_fields(required_edu)
        candidate_fields = self._extract_education_fields(candidate_edu)

        # Score based on degree level match
        degree_hierarchy = {
            'phd': 5, 'doctorate': 5,
            'master': 4, 'm.tech': 4, 'm.e': 4, 'm.sc': 4, 'msc': 4, 'mca': 4, 'mba': 4, 'ms': 4, 'ma': 4,
            'bachelor': 3, 'b.tech': 3, 'b.e': 3, 'b.sc': 3, 'bsc': 3, 'bca': 3, 'bba': 3, 'bs': 3, 'ba': 3, 'be': 3, 'bt': 3,
            'diploma': 2, 'associate': 2,
            'high school': 1, 'secondary': 1, 'hsc': 1, 'ssc': 1,
        }

        max_required_level = max((degree_hierarchy.get(l, 0) for l in required_levels), default=0)
        max_candidate_level = max((degree_hierarchy.get(l, 0) for l in candidate_levels), default=0)

        if max_required_level == 0:
            return 70.0  # No clear requirement

        if max_candidate_level >= max_required_level:
            # Candidate meets or exceeds degree level requirement
            # Check field match
            if required_fields and candidate_fields:
                field_match = any(self._fields_match(rf, cf) for rf in required_fields for cf in candidate_fields)
                if field_match:
                    return 100.0
                else:
                    return 90.0  # Right level, different field
            return 95.0  # Right level, no field info
        elif max_candidate_level >= max_required_level - 1:
            # One level below (e.g., Bachelor when Master required)
            return 60.0
        else:
            # Significantly below requirement
            return 30.0

    def _extract_degree_levels(self, education_list: List[str]) -> List[str]:
        """Extract degree level keywords from education strings."""
        levels = []
        degree_keywords = [
            'phd', 'doctorate', 'master', 'm.tech', 'm.e', 'm.sc', 'msc', 'mca', 'mba',
            'bachelor', 'b.tech', 'b.e', 'b.sc', 'bsc', 'bca', 'bba', 'bs', 'ba',
            'diploma', 'associate', 'high school', 'secondary', 'hsc', 'ssc'
        ]
        for edu in education_list:
            edu_lower = edu.lower()
            for kw in degree_keywords:
                if kw in edu_lower:
                    levels.append(kw)
        return levels

    def _extract_education_fields(self, education_list: List[str]) -> List[str]:
        """Extract field of study from education strings (most specific match wins)."""
        fields = []
        field_keywords = [
            'computer science', 'engineering', 'information technology', 'data science',
            'business', 'finance', 'arts', 'science', 'technology', 'mathematics',
            'statistics', 'physics', 'chemistry', 'biology', 'economics'
        ]
        # Sort by length descending so most specific (longest) fields match first
        field_keywords = sorted(field_keywords, key=len, reverse=True)
        for edu in education_list:
            edu_lower = edu.lower()
            for kw in field_keywords:
                if kw in edu_lower:
                    fields.append(kw)
                    # Only take the most specific match per education entry
                    # (e.g., "computer science" not "science" too)
                    break
        return fields

    def _fields_match(self, field1: str, field2: str) -> bool:
        """Check if two fields are related."""
        # Simple containment check
        if field1 in field2 or field2 in field1:
            return True
        # Related fields
        related_groups = [
            {'computer science', 'information technology', 'data science'},
            {'engineering', 'technology'},
            {'business', 'finance', 'economics'},
            {'arts', 'science'},
        ]
        for group in related_groups:
            if field1 in group and field2 in group:
                return True
        return False

    def _generate_explanations(self, skill_score: float, semantic_score: float,
                               experience_score: float, education_score: float,
                               pref_score: float, matched: List[str], missing: List[str],
                               missing_pref: List[str], job_req: JobRequirements) -> Tuple[List[str], List[str]]:
        """
        Generate human-readable explanations.

        Returns:
            (strengths, weaknesses)
        """
        strengths = []
        weaknesses = []

        # Skill-based
        if skill_score >= 80:
            strengths.append(f"Strong skills match: {len(matched)} of {len(matched) + len(missing)} required skills")
        elif skill_score >= 50:
            weaknesses.append(f"Partial skills match: missing {len(missing)} required skills")
        else:
            weaknesses.append(f"Weak skills match: missing {len(missing)} of {len(matched) + len(missing)} required skills")

        # Missing skills detail
        if missing:
            missing_display = ', '.join(missing[:5])
            if len(missing) > 5:
                missing_display += f" and {len(missing) - 5} more"
            weaknesses.append(f"Missing required skills: {missing_display}")

        # Semantic
        if semantic_score >= 70:
            strengths.append(f"Resume content strongly aligns with job description ({semantic_score:.0f}% semantic match)")
        elif semantic_score >= 40:
            weaknesses.append(f"Moderate alignment with job description ({semantic_score:.0f}%)")
        else:
            weaknesses.append(f"Low content alignment with job description ({semantic_score:.0f}%)")

        # Experience
        if experience_score >= 80:
            strengths.append(f"Meets or exceeds experience requirements ({job_req.required_experience}+ years)")
        elif experience_score >= 50:
            weaknesses.append(f"Partially meets experience requirements")
        else:
            weaknesses.append(f"Below experience requirements ({job_req.required_experience}+ years)")

        # Education
        if education_score >= 80:
            strengths.append("Education requirements satisfied")
        elif education_score >= 50:
            weaknesses.append("Education partially matches requirements")
        else:
            weaknesses.append("Education does not match requirements")

        # Preferred skills
        if pref_score >= 70:
            strengths.append(f"Has {len(missing_pref)} preferred skills")
        elif missing_pref:
            missing_pref_display = ', '.join(missing_pref[:3])
            if len(missing_pref) > 3:
                missing_pref_display += f" and {len(missing_pref) - 3} more"
            strengths.append(f"Could benefit from preferred skills: {missing_pref_display}")

        return strengths, weaknesses

    def _score_job_title(self, resume_text: str, job_description: str) -> float:
        """
        Score job title relevance based on keyword overlap in titles and summaries.

        Returns:
            Score 0-100 based on how well the candidate's background matches the job title
        """
        # Extract job title from job description (explicit "Job Title:" or "Position:" patterns only)
        import re

        job_title = ""
        # Try to find explicit job title - DO NOT fall back to first line
        for pattern in [r'Job Title:\s*(.+)', r'Position:\s*(.+)']:
            match = re.search(pattern, job_description, re.IGNORECASE | re.MULTILINE)
            if match:
                job_title = match.group(1).strip()
                break

        if not job_title:
            return 50.0  # Neutral if no explicit title found

        # Extract candidate's titles/roles from resume
        candidate_titles = []

        # Look for common title patterns in resume
        title_patterns = [
            r'(?i)(senior|lead|principal|staff|junior|entry.level)\s+\w+\s+(?:developer|engineer|scientist|analyst|architect|manager)',
            r'(?i)\w+\s+(?:developer|engineer|scientist|analyst|architect|manager)',
            r'(?i)(software|backend|frontend|full.stack|devops|data|ml|ai)\s+(?:developer|engineer|scientist)',
        ]

        for pattern in title_patterns:
            matches = re.findall(pattern, resume_text)
            candidate_titles.extend(matches)

        # Also check for explicit "Summary" or "Profile" sections
        summary_match = re.search(r'(?i)(summary|profile|objective):\s*(.+?)(?:\n\n|\n[A-Z]{2,}:|$)', resume_text, re.DOTALL)
        if summary_match:
            summary_text = summary_match.group(2).lower()
            # Extract role keywords from summary
            role_keywords = ['developer', 'engineer', 'scientist', 'analyst', 'architect', 'manager', 'lead', 'senior', 'junior']
            for kw in role_keywords:
                if kw in summary_text:
                    # Find the context around the keyword
                    idx = summary_text.index(kw)
                    start = max(0, idx - 30)
                    end = min(len(summary_text), idx + 30)
                    candidate_titles.append(summary_text[start:end].strip())

        if not candidate_titles:
            return 50.0  # Neutral if no titles found

        # Normalize job title for comparison
        job_title_lower = job_title.lower()

        # Key role terms to match
        role_terms = {
            'python': ['python', 'django', 'flask', 'fastapi'],
            'java': ['java', 'spring', 'spring boot'],
            'frontend': ['frontend', 'front-end', 'react', 'angular', 'vue', 'javascript', 'typescript'],
            'backend': ['backend', 'back-end', 'api', 'server', 'microservices'],
            'full.stack': ['full.stack', 'fullstack', 'full stack'],
            'devops': ['devops', 'sre', 'infrastructure', 'cloud', 'docker', 'kubernetes'],
            'data.scientist': ['data scientist', 'ml engineer', 'machine learning', 'ai engineer'],
            'data.analyst': ['data analyst', 'analytics', 'sql', 'tableau', 'power bi'],
            'mobile': ['mobile', 'ios', 'android', 'swift', 'kotlin', 'flutter', 'react native'],
            'qa': ['qa', 'test', 'quality assurance', 'automation'],
        }

        # Score based on role term overlap
        job_role_terms = set()
        for role, terms in role_terms.items():
            if any(t in job_title_lower for t in terms):
                job_role_terms.add(role)

        candidate_role_terms = set()
        for title in candidate_titles:
            title_lower = title.lower()
            for role, terms in role_terms.items():
                if any(t in title_lower for t in terms):
                    candidate_role_terms.add(role)

        if not job_role_terms:
            return 50.0  # Neutral if can't determine job role

        # Calculate overlap
        if not candidate_role_terms:
            return 30.0  # Low if no matching roles found

        overlap = job_role_terms & candidate_role_terms

        if len(overlap) >= len(job_role_terms):
            return 100.0  # Perfect match
        elif len(overlap) > 0:
            return 70.0   # Partial match
        else:
            return 20.0   # No role match

    def score_batch(self, resumes: List[Dict], job_description: str,
                    job_requirements: Optional[JobRequirements] = None) -> List[Dict]:
        """
        Score multiple candidates against a job.

        Args:
            resumes: List of dicts with 'id', 'text', and optionally 'name'
            job_description: Job description text
            job_requirements: Pre-analyzed job requirements

        Returns:
            List of scored candidate dicts
        """
        if job_requirements is None:
            job_requirements = self.job_analyzer.analyze(job_description)

        results = []
        for resume in resumes:
            score = self.score_candidate(
                resume.get('text', ''),
                job_description,
                job_requirements
            )
            results.append({
                'id': resume.get('id'),
                'name': resume.get('name', ''),
                'score': score.to_dict(),
                'overall_score': score.overall_score
            })

        # Sort by overall score descending
        results.sort(key=lambda x: x['overall_score'], reverse=True)

        return results


def create_scoring_engine(weights: Optional[Dict[str, float]] = None) -> ScoringEngine:
    """
    Create a scoring engine with the given weights.

    Args:
        weights: Custom scoring weights

    Returns:
        ScoringEngine instance
    """
    return ScoringEngine(weights=weights)
