"""
Similarity Engine Module
Computes semantic similarity between resume and job description using TF-IDF and cosine similarity.
"""

import logging
import pickle
import numpy as np
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .text_preprocessor import TextPreprocessor
from .skill_extractor import SkillExtractor

logger = logging.getLogger(__name__)


class SimilarityEngine:
    """
    Computes semantic similarity between resume and job description.

    Uses TF-IDF vectorization with cosine similarity, with optional
    skill-based boosting for more accurate matching.
    """

    def __init__(self, max_features: int = 5000, ngram_range: Tuple[int, int] = (1, 2),
                 min_df: int = 1, max_df: float = 0.95,
                 preprocessor: Optional[TextPreprocessor] = None,
                 skill_extractor: Optional[SkillExtractor] = None):
        """
        Initialize the similarity engine.

        Args:
            max_features: Maximum TF-IDF features
            ngram_range: N-gram range for vectorization
            min_df: Minimum document frequency
            max_df: Maximum document frequency (ignore too common terms)
            preprocessor: TextPreprocessor instance
            skill_extractor: SkillExtractor instance
        """
        self.max_features = max_features
        self.ngram_range = ngram_range
        self.min_df = min_df
        self.max_df = max_df

        self.preprocessor = preprocessor or TextPreprocessor()
        self.skill_extractor = skill_extractor or SkillExtractor()

        # TF-IDF Vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=max_features,
            ngram_range=ngram_range,
            min_df=min_df,
            max_df=max_df,
            lowercase=True,
            strip_accents='unicode',
            analyzer='word',
            token_pattern=r'(?u)\b[a-zA-Z0-9\-\+\#\.]{2,}\b'
        )

        # Fitted state
        self._fitted = False
        self._job_vectors = None
        self._job_texts = None

    def fit(self, job_texts: List[str]):
        """
        Fit the vectorizer on job descriptions.

        Args:
            job_texts: List of job description texts
        """
        if not job_texts:
            logger.warning("No job texts provided for fitting")
            return

        # Preprocess job texts
        processed_texts = [self.preprocessor.clean_for_tfidf(text) for text in job_texts]

        # Fit vectorizer
        self.vectorizer.fit(processed_texts)
        self._job_vectors = self.vectorizer.transform(processed_texts)
        self._job_texts = job_texts
        self._fitted = True

        logger.info(f"Fitted vectorizer on {len(job_texts)} job descriptions")

    def transform(self, texts: List[str]):
        """
        Transform texts to TF-IDF vectors.

        Args:
            texts: List of texts to transform

        Returns:
            Sparse matrix of TF-IDF vectors
        """
        processed_texts = [self.preprocessor.clean_for_tfidf(text) for text in texts]
        return self.vectorizer.transform(processed_texts)

    def compute_similarity(self, resume_text: str, job_text: str,
                           use_skills: bool = True, skill_weight: float = 0.3) -> float:
        """
        Compute similarity between a resume and job description.

        Args:
            resume_text: Resume text
            job_text: Job description text
            use_skills: Whether to incorporate skill overlap
            skill_weight: Weight for skill-based similarity (0-1)

        Returns:
            Similarity score (0-100)
        """
        # TF-IDF cosine similarity
        resume_processed = self.preprocessor.clean_for_tfidf(resume_text)
        job_processed = self.preprocessor.clean_for_tfidf(job_text)

        if not resume_processed or not job_processed:
            return 0.0

        # Auto-fit vectorizer on both texts if not fitted
        # Use a temporary vectorizer with adjusted parameters for single-pair comparison
        if not self._fitted:
            # Fit on both documents together for proper TF-IDF
            from sklearn.feature_extraction.text import TfidfVectorizer
            temp_vectorizer = TfidfVectorizer(
                max_features=self.max_features,
                ngram_range=self.ngram_range,
                min_df=1,
                max_df=1.0,  # Allow all terms when only 2 docs
                lowercase=True,
                strip_accents='unicode',
                analyzer='word',
                token_pattern=r'(?u)\b[a-zA-Z0-9\-\+\#\.]{2,}\b'
            )
            temp_vectorizer.fit([resume_processed, job_processed])
            vectors = temp_vectorizer.transform([resume_processed, job_processed])
        else:
            vectors = self.vectorizer.transform([resume_processed, job_processed])

        tfidf_sim = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

        if not use_skills:
            return float(tfidf_sim * 100)

        # Skill-based similarity
        skill_sim = self._compute_skill_similarity(resume_text, job_text)

        # Combined similarity
        combined = (1 - skill_weight) * tfidf_sim + skill_weight * skill_sim

        return float(combined * 100)

    def _compute_skill_similarity(self, resume_text: str, job_text: str) -> float:
        """
        Compute skill overlap similarity using Jaccard index.

        Args:
            resume_text: Resume text
            job_text: Job description text

        Returns:
            Jaccard similarity (0-1)
        """
        # Extract skills from both
        resume_skills = set(self.skill_extractor.extract_skills(resume_text).get('skills', []))
        job_skills = set(self.skill_extractor.extract_skills(job_text).get('skills', []))

        if not job_skills:
            return 1.0  # If no skills required, perfect match

        if not resume_skills:
            return 0.0  # If no skills in resume, no match

        # Jaccard similarity: intersection / union
        intersection = len(resume_skills & job_skills)
        union = len(resume_skills | job_skills)

        return intersection / union if union > 0 else 0.0

    def compute_batch_similarity(self, resume_texts: List[str], job_text: str,
                                  use_skills: bool = True) -> List[float]:
        """
        Compute similarity for multiple resumes against one job.

        Args:
            resume_texts: List of resume texts
            job_text: Job description text
            use_skills: Whether to incorporate skill overlap

        Returns:
            List of similarity scores (0-100)
        """
        scores = []
        for resume_text in resume_texts:
            score = self.compute_similarity(resume_text, job_text, use_skills)
            scores.append(score)
        return scores

    def rank_candidates(self, candidates: List[Dict], job_text: str,
                        use_skills: bool = True) -> List[Dict]:
        """
        Rank candidates by similarity to job.

        Args:
            candidates: List of candidate dicts with 'text' and 'id' fields
            job_text: Job description text
            use_skills: Whether to incorporate skill overlap

        Returns:
            List of candidates sorted by similarity (highest first)
        """
        ranked = []
        for candidate in candidates:
            text = candidate.get('text', '')
            score = self.compute_similarity(text, job_text, use_skills)
            ranked.append({
                **candidate,
                'similarity_score': score
            })

        # Sort by score descending
        ranked.sort(key=lambda x: x['similarity_score'], reverse=True)
        return ranked

    def get_feature_importance(self, resume_text: str, job_text: str, top_n: int = 20) -> List[Tuple[str, float]]:
        """
        Get most important features (terms) contributing to similarity.

        Args:
            resume_text: Resume text
            job_text: Job description text
            top_n: Number of top features to return

        Returns:
            List of (feature, importance) tuples
        """
        resume_processed = self.preprocessor.clean_for_tfidf(resume_text)
        job_processed = self.preprocessor.clean_for_tfidf(job_text)

        # Transform
        vectors = self.vectorizer.transform([resume_processed, job_processed])

        # Get feature names
        feature_names = self.vectorizer.get_feature_names_out()

        # Get non-zero features for both
        resume_vec = vectors[0].toarray()[0]
        job_vec = vectors[1].toarray()[0]

        # Find common non-zero features
        common_indices = np.where((resume_vec > 0) & (job_vec > 0))[0]

        if len(common_indices) == 0:
            return []

        # Score by product of TF-IDF values
        scores = [(feature_names[i], resume_vec[i] * job_vec[i]) for i in common_indices]
        scores.sort(key=lambda x: x[1], reverse=True)

        return scores[:top_n]

    def save(self, filepath: str):
        """Save the fitted vectorizer to disk."""
        data = {
            'vectorizer': self.vectorizer,
            'fitted': self._fitted,
            'max_features': self.max_features,
            'ngram_range': self.ngram_range,
            'min_df': self.min_df,
            'max_df': self.max_df
        }
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        logger.info(f"Similarity engine saved to {filepath}")

    @classmethod
    def load(cls, filepath: str) -> 'SimilarityEngine':
        """Load a fitted similarity engine from disk."""
        with open(filepath, 'rb') as f:
            data = pickle.load(f)

        engine = cls(
            max_features=data['max_features'],
            ngram_range=data['ngram_range'],
            min_df=data['min_df'],
            max_df=data['max_df']
        )
        engine.vectorizer = data['vectorizer']
        engine._fitted = data['fitted']

        logger.info(f"Similarity engine loaded from {filepath}")
        return engine


def compute_similarity(resume_text: str, job_text: str) -> float:
    """
    Convenience function to compute similarity.

    Args:
        resume_text: Resume text
        job_text: Job description text

    Returns:
        Similarity score (0-100)
    """
    engine = SimilarityEngine()
    return engine.compute_similarity(resume_text, job_text)