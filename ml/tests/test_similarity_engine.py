"""
Unit tests for SimilarityEngine module.
"""

import pytest
from ml.similarity_engine import SimilarityEngine
from ml.skill_extractor import SkillExtractor
from ml.text_preprocessor import TextPreprocessor


class TestSimilarityEngine:
    """Tests for SimilarityEngine class."""

    @pytest.fixture
    def engine(self):
        skill_extractor = SkillExtractor()
        preprocessor = TextPreprocessor()
        return SimilarityEngine(skill_extractor=skill_extractor, preprocessor=preprocessor)

    # --- Basic Similarity Tests ---

    def test_similarity_identical_texts(self, engine):
        """Test similarity of identical texts."""
        text = "Python developer with Django and PostgreSQL experience"
        score = engine.compute_similarity(text, text)

        assert score == 100.0

    def test_similarity_very_similar(self, engine):
        """Test similarity of very similar texts."""
        text1 = "Python developer with Django and PostgreSQL experience"
        text2 = "Python developer with Django and Postgres experience"

        score = engine.compute_similarity(text1, text2)

        assert score >= 60  # Should be reasonably high similarity

    def test_similarity_different_texts(self, engine):
        """Test similarity of completely different texts."""
        text1 = "Python developer with Django experience"
        text2 = "Mechanical engineer with AutoCAD and SolidWorks experience"

        score = engine.compute_similarity(text1, text2)

        assert score < 50  # Should be low similarity

    def test_similarity_empty_text(self, engine):
        """Test similarity with empty text."""
        score = engine.compute_similarity("", "Python developer")

        assert score == 0.0

    def test_similarity_both_empty(self, engine):
        """Test similarity of two empty texts."""
        score = engine.compute_similarity("", "")

        assert score == 0.0

    # --- Skill-Aware Similarity Tests ---

    def test_similarity_with_skills_boost(self, engine):
        """Test that skill overlap boosts similarity."""
        resume = "Python Django REST API PostgreSQL Git"
        job = "Required: Python Django REST API PostgreSQL Git"

        # With skills should be higher
        score_with_skills = engine.compute_similarity(resume, job, use_skills=True)
        score_without_skills = engine.compute_similarity(resume, job, use_skills=False)

        assert score_with_skills >= score_without_skills

    def test_similarity_skill_overlap_only(self, engine):
        """Test similarity when only skills overlap."""
        resume = "Python Django Flask"
        job = "Python Django Flask"

        score = engine.compute_similarity(resume, job, use_skills=True)

        assert score >= 90

    # --- Preprocessing Integration Tests ---

    def test_preprocessing_removes_stopwords(self, engine):
        """Test that preprocessing removes stopwords for TF-IDF."""
        text1 = "the python developer with django"
        text2 = "python developer django"

        score = engine.compute_similarity(text1, text2)

        # Stopwords removed, should be very similar
        assert score >= 80

    def test_preprocessing_handles_punctuation(self, engine):
        """Test that preprocessing handles punctuation."""
        text1 = "Python, Django; PostgreSQL!"
        text2 = "Python Django PostgreSQL"

        score = engine.compute_similarity(text1, text2)

        assert score >= 90

    def test_preprocessing_case_insensitive(self, engine):
        """Test that preprocessing is case insensitive."""
        text1 = "PYTHON DJANGO POSTGRESQL"
        text2 = "python django postgresql"

        score = engine.compute_similarity(text1, text2)

        assert score == 100.0

    # --- Edge Cases ---

    def test_similarity_very_short_texts(self, engine):
        """Test similarity with very short texts."""
        text1 = "Python"
        text2 = "Python"

        score = engine.compute_similarity(text1, text2)

        assert score >= 50  # Short texts may not give perfect score

    def test_similarity_single_word_different(self, engine):
        """Test similarity of single different words."""
        score = engine.compute_similarity("Python", "Java")

        assert score < 50

    def test_similarity_long_texts(self, engine):
        """Test similarity with long texts."""
        # Create long texts with repeated content
        base = "Python Django REST API PostgreSQL Git Docker AWS. " * 20
        text1 = base + "Senior developer with 5 years experience."
        text2 = base + "Lead engineer with 6 years experience."

        score = engine.compute_similarity(text1, text2)

        assert score >= 70  # Should be similar due to common base

    def test_similarity_special_characters(self, engine):
        """Test similarity with special characters in skills."""
        text1 = "C++ C# .NET Node.js"
        text2 = "C++ C# .NET Node.js"

        score = engine.compute_similarity(text1, text2)

        assert score >= 80

    # --- Vectorizer Behavior Tests ---

    def test_vectorizer_fitted_on_first_call(self, engine):
        """Test that vectorizer is fitted on first call."""
        text1 = "Python Django"
        text2 = "Python Flask"

        score1 = engine.compute_similarity(text1, text2)
        score2 = engine.compute_similarity(text1, text2)

        # Second call should use already fitted vectorizer
        assert score1 == score2

    def test_vectorizer_handles_unseen_vocabulary(self, engine):
        """Test vectorizer handles words not seen during fitting."""
        # First call with some vocabulary
        engine.compute_similarity("Python Django", "Python Flask")

        # Second call with new words
        score = engine.compute_similarity("Java Spring", "Java Hibernate")

        assert score >= 0  # Should not crash


class TestSimilarityEngineWithRealResumes:
    """Tests with more realistic resume/job description pairs."""

    @pytest.fixture
    def engine(self):
        skill_extractor = SkillExtractor()
        preprocessor = TextPreprocessor()
        return SimilarityEngine(skill_extractor=skill_extractor, preprocessor=preprocessor)

    @pytest.fixture
    def python_job(self):
        return """Job Title: Python Developer
We are seeking a skilled Python Developer to join our backend engineering team.

Requirements:
- 3+ years of experience with Python
- Strong knowledge of Django or Flask web frameworks
- Experience with REST API development
- Familiarity with PostgreSQL and ORM
- Knowledge of Git and CI/CD pipelines

Preferred:
- Experience with FastAPI
- Knowledge of Docker and AWS
- Familiarity with Celery for async tasks

Required Skills: Python, Django, REST API, PostgreSQL, Git
Preferred Skills: FastAPI, Docker, AWS, Celery, Flask, Redis
Experience Required: 3 years
Education Required: B.Tech Computer Science"""

    def test_strong_candidate_similarity(self, engine, python_job):
        """Test similarity for strong Python candidate."""
        resume = """SENIOR PYTHON DEVELOPER
Summary: Senior Python Developer with 6 years experience building scalable backend systems.

Education: B.Tech Computer Science, 2017

Skills: Python, Django, REST API, PostgreSQL, Git, Docker, AWS, FastAPI, Celery

Experience:
Senior Python Developer, BigTech (2017-Present)
- Built Python Django applications serving millions of users
- Designed REST APIs with Django REST Framework
- Used PostgreSQL for data storage
- Deployed on AWS with Docker containers
- Implemented async tasks with Celery"""

        score = engine.compute_similarity(resume, python_job, use_skills=True)

        assert score >= 40  # Should be reasonably similar (actual is ~45-50)

    def test_weak_candidate_similarity(self, engine, python_job):
        """Test similarity for weak candidate (different field)."""
        resume = """MECHANICAL ENGINEER
Summary: Mechanical Design Engineer with 5 years experience.

Education: Diploma in Mechanical Engineering, 2019

Skills: AutoCAD, Mechanical Design, Quality Control, Manufacturing, SolidWorks

Experience:
Design Engineer, MechWorks (2019-Present)
- Created 2D drawings with AutoCAD
- Performed quality inspections"""

        score = engine.compute_similarity(resume, python_job, use_skills=True)

        assert score < 40  # Should be quite different

    def test_moderate_candidate_similarity(self, engine, python_job):
        """Test similarity for moderate candidate (related field)."""
        resume = """DATA ANALYST
Summary: Data Analyst with 3 years experience.

Education: B.Tech Computer Science, 2020

Skills: SQL, Python, pandas, Excel, Tableau, Statistics

Experience:
Data Analyst, DataCorp (2020-Present)
- Analyzed data with Python and SQL
- Built Tableau dashboards"""

        score = engine.compute_similarity(resume, python_job, use_skills=True)

        # Should have some similarity (Python, CS degree) - actual is ~15-20
        assert 5 <= score <= 40

    def test_frontend_candidate_similarity(self, engine, python_job):
        """Test similarity for frontend developer."""
        resume = """FRONTEND DEVELOPER
Summary: Frontend Developer with React experience.

Education: B.Tech Computer Science, 2019

Skills: JavaScript, React, HTML, CSS, TypeScript

Experience:
Frontend Developer, WebCo (2019-Present)
- Built React applications
- Used TypeScript and CSS"""

        score = engine.compute_similarity(resume, python_job, use_skills=True)

        # Some overlap (CS degree, programming) but different stack - actual ~10
        assert 5 <= score <= 30


if __name__ == '__main__':
    pytest.main([__file__, '-v'])