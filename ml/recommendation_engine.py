"""
Recommendation Engine Module
Generates hiring recommendations based on scores with configurable thresholds.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum

from .scoring_engine import ScoringEngine, ScoreBreakdown

logger = logging.getLogger(__name__)


class Recommendation(Enum):
    """Hiring recommendation levels."""
    HIGHLY_RECOMMENDED = "Highly Recommended"
    RECOMMENDED = "Recommended"
    CONSIDER = "Consider"
    NOT_RECOMMENDED = "Not Recommended"


# Default thresholds (can be overridden)
DEFAULT_THRESHOLDS = {
    'highly_recommended': 90,
    'recommended': 80,
    'consider': 65,
    # Below 65 = Not Recommended
}


@dataclass
class RecommendationResult:
    """Complete recommendation with rationale."""
    recommendation: Recommendation
    overall_score: float
    confidence: float
    rationale: str
    key_factors: List[str]
    concerns: List[str]
    disclaimer: str = ("This is an AI-assisted decision support tool. "
                        "Final hiring decisions should be made by qualified human evaluators. "
                        "This system does not consider protected characteristics and is designed "
                        "to reduce bias, but human oversight is essential.")


class RecommendationEngine:
    """
    Generates hiring recommendations based on screening scores.

    Uses configurable thresholds and provides explainable rationale
    for each recommendation.
    """

    def __init__(self, thresholds: Optional[Dict[str, float]] = None,
                 scoring_engine: Optional[ScoringEngine] = None):
        """
        Initialize the recommendation engine.

        Args:
            thresholds: Custom score thresholds
            scoring_engine: ScoringEngine instance
        """
        self.thresholds = thresholds or DEFAULT_THRESHOLDS.copy()
        self.scoring_engine = scoring_engine or ScoringEngine()

    def recommend(self, score_breakdown: ScoreBreakdown) -> RecommendationResult:
        """
        Generate a recommendation from a score breakdown.

        Args:
            score_breakdown: ScoreBreakdown from ScoringEngine

        Returns:
            RecommendationResult with recommendation and explanation
        """
        score = score_breakdown.overall_score

        # Determine recommendation
        if score >= self.thresholds['highly_recommended']:
            recommendation = Recommendation.HIGHLY_RECOMMENDED
            confidence = min(0.95, score / 100)
        elif score >= self.thresholds['recommended']:
            recommendation = Recommendation.RECOMMENDED
            confidence = 0.8
        elif score >= self.thresholds['consider']:
            recommendation = Recommendation.CONSIDER
            confidence = 0.65
        else:
            recommendation = Recommendation.NOT_RECOMMENDED
            confidence = max(0.5, 1 - score / 100)

        # Generate rationale
        rationale = self._generate_rationale(score_breakdown, recommendation)

        # Extract key factors
        key_factors = self._extract_key_factors(score_breakdown, recommendation)

        # Extract concerns
        concerns = self._extract_concerns(score_breakdown)

        return RecommendationResult(
            recommendation=recommendation,
            overall_score=score,
            confidence=confidence,
            rationale=rationale,
            key_factors=key_factors,
            concerns=concerns
        )

    def _generate_rationale(self, breakdown: ScoreBreakdown, recommendation: Recommendation) -> str:
        """Generate human-readable rationale for the recommendation."""
        score = breakdown.overall_score
        parts = []

        # Overall assessment
        if recommendation == Recommendation.HIGHLY_RECOMMENDED:
            parts.append(f"This candidate scores {score:.0f}% overall, indicating an excellent match for the role.")
        elif recommendation == Recommendation.RECOMMENDED:
            parts.append(f"This candidate scores {score:.0f}% overall, indicating a good match for the role.")
        elif recommendation == Recommendation.CONSIDER:
            parts.append(f"This candidate scores {score:.0f}% overall, indicating a moderate match that warrants further review.")
        else:
            parts.append(f"This candidate scores {score:.0f}% overall, indicating the role may not be a strong fit.")

        # Skill match
        if breakdown.skill_score >= 70:
            parts.append(f"Skills alignment is strong ({breakdown.skill_score:.0f}%), with {len(breakdown.matched_skills)} required skills matched.")
        elif breakdown.skill_score >= 40:
            parts.append(f"Skills alignment is moderate ({breakdown.skill_score:.0f}%), with some gaps in required skills.")
        else:
            parts.append(f"Skills alignment is weak ({breakdown.skill_score:.0f}%), missing several required skills.")

        # Semantic match
        if breakdown.semantic_score >= 60:
            parts.append(f"Resume content strongly aligns with the job description ({breakdown.semantic_score:.0f}%).")
        elif breakdown.semantic_score >= 35:
            parts.append(f"Resume content has moderate alignment with the job description ({breakdown.semantic_score:.0f}%).")
        else:
            parts.append(f"Resume content has limited alignment with the job description ({breakdown.semantic_score:.0f}%).")

        # Experience
        if breakdown.experience_score >= 80:
            parts.append("Candidate meets or exceeds experience requirements.")
        elif breakdown.experience_score >= 50:
            parts.append("Candidate partially meets experience requirements.")
        else:
            parts.append("Candidate falls short of experience requirements.")

        # Education
        if breakdown.education_score >= 80:
            parts.append("Education requirements are satisfied.")
        elif breakdown.education_score >= 50:
            parts.append("Education partially matches requirements.")
        else:
            parts.append("Education does not match the stated requirements.")

        # Preferred skills
        if breakdown.missing_preferred_skills:
            parts.append(f"Candidate could benefit from preferred skills: {', '.join(breakdown.missing_preferred_skills[:3])}.")
        elif breakdown.preferred_skill_score >= 70:
            parts.append("Candidate possesses preferred skills for the role.")

        return ' '.join(parts)

    def _extract_key_factors(self, breakdown: ScoreBreakdown, recommendation: Recommendation) -> List[str]:
        """Extract positive factors supporting the recommendation."""
        factors = []

        if breakdown.matched_skills:
            factors.append(f"Matched {len(breakdown.matched_skills)} required skills: {', '.join(breakdown.matched_skills[:5])}")

        if breakdown.semantic_score >= 60:
            factors.append(f"High semantic similarity ({breakdown.semantic_score:.0f}%)")

        if breakdown.experience_score >= 80:
            factors.append("Meets/exceeds experience requirements")

        if breakdown.education_score >= 80:
            factors.append("Satisfies education requirements")

        if breakdown.preferred_skill_score >= 60:
            factors.append(f"Has {len([s for s in breakdown.matched_skills if s in breakdown.missing_preferred_skills])} preferred skills")

        # Don't duplicate from breakdown.strengths - use custom factors only
        return factors

    def _extract_concerns(self, breakdown: ScoreBreakdown) -> List[str]:
        """Extract concerns or gaps."""
        concerns = []

        if breakdown.missing_skills:
            missing_display = ', '.join(breakdown.missing_skills[:5])
            if len(breakdown.missing_skills) > 5:
                missing_display += f" and {len(breakdown.missing_skills) - 5} more"
            concerns.append(f"Missing required skills: {missing_display}")

        if breakdown.semantic_score < 40:
            concerns.append(f"Low content alignment with job ({breakdown.semantic_score:.0f}%)")

        if breakdown.experience_score < 60:
            concerns.append("Below experience requirements")

        if breakdown.education_score < 60:
            concerns.append("Education may not match requirements")

        # Don't duplicate from breakdown.weaknesses - already handled above
        return concerns

    def recommend_batch(self, score_breakdowns: List[ScoreBreakdown]) -> List[RecommendationResult]:
        """
        Generate recommendations for multiple candidates.

        Args:
            score_breakdowns: List of ScoreBreakdown objects

        Returns:
            List of RecommendationResult objects
        """
        results = []
        for breakdown in score_breakdowns:
            results.append(self.recommend(breakdown))
        return results

    def rank_with_recommendations(self, scored_candidates: List[Dict]) -> List[Dict]:
        """
        Add recommendations to already scored candidates and sort.

        Args:
            scored_candidates: List of candidates with 'score' (ScoreBreakdown) field

        Returns:
            Sorted list with recommendations added
        """
        for candidate in scored_candidates:
            score = candidate.get('score')
            if isinstance(score, ScoreBreakdown):
                rec = self.recommend(score)
                candidate['recommendation'] = rec.recommendation.value
                candidate['confidence'] = rec.confidence
                candidate['rationale'] = rec.rationale
                candidate['key_factors'] = rec.key_factors
                candidate['concerns'] = rec.concerns

        # Sort by overall score descending
        scored_candidates.sort(key=lambda x: x.get('overall_score', 0), reverse=True)

        return scored_candidates


def get_recommendation(score_breakdown: ScoreBreakdown,
                       thresholds: Optional[Dict[str, float]] = None) -> RecommendationResult:
    """
    Convenience function to get a recommendation.

    Args:
        score_breakdown: ScoreBreakdown object
        thresholds: Optional custom thresholds

    Returns:
        RecommendationResult
    """
    engine = RecommendationEngine(thresholds=thresholds)
    return engine.recommend(score_breakdown)