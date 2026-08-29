"""
ML Package for Hire Smart - AI-powered Resume Screening

This package provides:
- Resume parsing (PDF/DOCX)
- Text preprocessing (spaCy-based)
- Skill extraction (configurable dictionary)
- Job description analysis
- Semantic similarity (TF-IDF + Cosine)
- Hybrid scoring (40/25/15/10/10 weights)
- Explainable AI recommendations
"""

from .resume_parser import ResumeParser, parse_resume
from .text_preprocessor import TextPreprocessor, get_preprocessor
from .skill_extractor import SkillExtractor, create_skill_extractor
from .job_analyzer import JobAnalyzer, JobRequirements, analyze_job
from .similarity_engine import SimilarityEngine, compute_similarity
from .scoring_engine import ScoringEngine, ScoreBreakdown, create_scoring_engine
from .recommendation_engine import (
    RecommendationEngine,
    RecommendationResult,
    Recommendation,
    get_recommendation
)
from .pipeline import ScreeningPipeline, quick_screen, create_pipeline

__version__ = '1.0.0'

__all__ = [
    # Resume Parser
    'ResumeParser',
    'parse_resume',
    # Text Preprocessor
    'TextPreprocessor',
    'get_preprocessor',
    # Skill Extractor
    'SkillExtractor',
    'create_skill_extractor',
    # Job Analyzer
    'JobAnalyzer',
    'JobRequirements',
    'analyze_job',
    # Similarity Engine
    'SimilarityEngine',
    'compute_similarity',
    # Scoring Engine
    'ScoringEngine',
    'ScoreBreakdown',
    'create_scoring_engine',
    # Recommendation Engine
    'RecommendationEngine',
    'RecommendationResult',
    'Recommendation',
    'get_recommendation',
    # Pipeline
    'ScreeningPipeline',
    'quick_screen',
    'create_pipeline',
]