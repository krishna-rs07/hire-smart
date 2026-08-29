"""
ML Pipeline Module
High-level pipeline that orchestrates all ML components for end-to-end screening.
"""

import logging
from typing import Dict, List, Optional
from dataclasses import dataclass, field

from .resume_parser import ResumeParser, parse_resume
from .skill_extractor import SkillExtractor
from .text_preprocessor import TextPreprocessor
from .job_analyzer import JobAnalyzer, JobRequirements
from .similarity_engine import SimilarityEngine
from .scoring_engine import ScoringEngine, ScoreBreakdown
from .recommendation_engine import RecommendationEngine, RecommendationResult

logger = logging.getLogger(__name__)


@dataclass
class ScreeningResult:
    """Complete screening result for a candidate-job pair."""
    candidate_id: int
    job_id: int
    candidate_name: str
    job_title: str

    # Scores
    overall_score: float = 0.0
    skill_score: float = 0.0
    semantic_score: float = 0.0
    experience_score: float = 0.0
    education_score: float = 0.0
    preferred_skill_score: float = 0.0

    # Skill details
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    missing_preferred_skills: List[str] = field(default_factory=list)

    # Explanation
    explanation: str = ""
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)

    # Recommendation
    recommendation: str = "Not Recommended"
    confidence: float = 0.0

    # Metadata
    error: Optional[str] = None


class ScreeningPipeline:
    """
    End-to-end screening pipeline.

    Orchestrates:
    1. Resume text extraction
    2. Job requirement analysis
    3. Skill extraction
    4. Semantic similarity
    5. Hybrid scoring
    6. Recommendation generation
    """

    def __init__(self,
                 skill_extractor: Optional[SkillExtractor] = None,
                 preprocessor: Optional[TextPreprocessor] = None,
                 job_analyzer: Optional[JobAnalyzer] = None,
                 similarity_engine: Optional[SimilarityEngine] = None,
                 scoring_engine: Optional[ScoringEngine] = None,
                 recommendation_engine: Optional[RecommendationEngine] = None):
        """
        Initialize the pipeline with all components.

        Args:
            skill_extractor: SkillExtractor instance
            preprocessor: TextPreprocessor instance
            job_analyzer: JobAnalyzer instance
            similarity_engine: SimilarityEngine instance
            scoring_engine: ScoringEngine instance
            recommendation_engine: RecommendationEngine instance
        """
        self.skill_extractor = skill_extractor or SkillExtractor()
        self.preprocessor = preprocessor or TextPreprocessor()
        self.job_analyzer = job_analyzer or JobAnalyzer(
            skill_extractor=self.skill_extractor,
            preprocessor=self.preprocessor
        )
        self.similarity_engine = similarity_engine or SimilarityEngine(
            skill_extractor=self.skill_extractor,
            preprocessor=self.preprocessor
        )
        self.scoring_engine = scoring_engine or ScoringEngine(
            skill_extractor=self.skill_extractor,
            similarity_engine=self.similarity_engine,
            job_analyzer=self.job_analyzer
        )
        self.recommendation_engine = recommendation_engine or RecommendationEngine(
            scoring_engine=self.scoring_engine
        )

        self.resume_parser = ResumeParser()

    def screen_resume(self, resume_file_path: str, job_description: str,
                      job_requirements: Optional[JobRequirements] = None,
                      candidate_name: str = "", job_title: str = "") -> ScreeningResult:
        """
        Screen a single resume against a job.

        Args:
            resume_file_path: Path to resume file (PDF/DOCX)
            job_description: Job description text
            job_requirements: Pre-analyzed job requirements (optional)
            candidate_name: Candidate name (for result)
            job_title: Job title (for result)

        Returns:
            ScreeningResult with all details
        """
        try:
            # 1. Extract text from resume
            resume_text, metadata = self.resume_parser.extract_text(resume_file_path)

            if not resume_text or len(resume_text.strip()) < 50:
                return ScreeningResult(
                    candidate_id=0,
                    job_id=0,
                    candidate_name=candidate_name or "Unknown",
                    job_title=job_title or "Unknown",
                    error="Failed to extract sufficient text from resume"
                )

            # 2. Analyze job requirements if not provided
            if job_requirements is None:
                job_requirements = self.job_analyzer.analyze(job_description)

            # 3. Score candidate
            score_breakdown = self.scoring_engine.score_candidate(
                resume_text, job_description, job_requirements
            )

            # 4. Generate recommendation
            recommendation = self.recommendation_engine.recommend(score_breakdown)

            # 5. Build result
            return ScreeningResult(
                candidate_id=0,
                job_id=0,
                candidate_name=candidate_name or "Unknown",
                job_title=job_title or "Unknown",
                overall_score=score_breakdown.overall_score,
                skill_score=score_breakdown.skill_score,
                semantic_score=score_breakdown.semantic_score,
                experience_score=score_breakdown.experience_score,
                education_score=score_breakdown.education_score,
                preferred_skill_score=score_breakdown.preferred_skill_score,
                matched_skills=score_breakdown.matched_skills,
                missing_skills=score_breakdown.missing_skills,
                missing_preferred_skills=score_breakdown.missing_preferred_skills,
                explanation=recommendation.rationale,
                strengths=recommendation.key_factors,
                weaknesses=recommendation.concerns,
                recommendation=recommendation.recommendation.value,
                confidence=recommendation.confidence
            )

        except Exception as e:
            logger.error(f"Error screening resume: {e}")
            return ScreeningResult(
                candidate_id=0,
                job_id=0,
                candidate_name=candidate_name or "Unknown",
                job_title=job_title or "Unknown",
                error=str(e)
            )

    def screen_batch(self, resume_files: List[str], job_description: str,
                     job_requirements: Optional[JobRequirements] = None) -> List[ScreeningResult]:
        """
        Screen multiple resumes against a job.

        Args:
            resume_files: List of (file_path, candidate_name) tuples
            job_description: Job description text
            job_requirements: Pre-analyzed job requirements (optional)

        Returns:
            List of ScreeningResult objects, sorted by score
        """
        if job_requirements is None:
            job_requirements = self.job_analyzer.analyze(job_description)

        results = []
        for item in resume_files:
            if isinstance(item, tuple):
                file_path, name = item
            else:
                file_path = item
                name = ""

            result = self.screen_resume(file_path, job_description, job_requirements, candidate_name=name)
            results.append(result)

        # Sort by overall score descending
        results.sort(key=lambda x: x.overall_score, reverse=True)
        return results

    def get_job_requirements(self, job_description: str) -> JobRequirements:
        """Extract and return job requirements."""
        return self.job_analyzer.analyze(job_description)


def create_pipeline() -> ScreeningPipeline:
    """Create a default screening pipeline."""
    return ScreeningPipeline()


def quick_screen(resume_text: str, job_description: str) -> Dict:
    """
    Quick screening without file parsing (for already extracted text).

    Args:
        resume_text: Already extracted resume text
        job_description: Job description text

    Returns:
        Dictionary with screening results
    """
    pipeline = create_pipeline()

    # Analyze job
    job_req = pipeline.job_analyzer.analyze(job_description)

    # Score
    score = pipeline.scoring_engine.score_candidate(resume_text, job_description, job_req)

    # Recommend
    rec = pipeline.recommendation_engine.recommend(score)

    return {
        'overall_score': score.overall_score,
        'skill_score': score.skill_score,
        'semantic_score': score.semantic_score,
        'experience_score': score.experience_score,
        'education_score': score.education_score,
        'preferred_skill_score': score.preferred_skill_score,
        'job_title_score': score.job_title_score,
        'matched_skills': score.matched_skills,
        'missing_skills': score.missing_skills,
        'missing_preferred_skills': score.missing_preferred_skills,
        'recommendation': rec.recommendation.value,
        'confidence': rec.confidence,
        'rationale': rec.rationale,
        'strengths': rec.key_factors,
        'concerns': rec.concerns,
        'disclaimer': rec.disclaimer
    }