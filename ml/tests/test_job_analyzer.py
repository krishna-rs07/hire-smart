"""
Unit tests for JobAnalyzer module.
"""

import pytest
from ml.job_analyzer import JobAnalyzer
from ml.skill_extractor import SkillExtractor
from ml.text_preprocessor import TextPreprocessor


class TestJobAnalyzer:
    """Tests for JobAnalyzer class."""

    @pytest.fixture
    def analyzer(self):
        skill_extractor = SkillExtractor()
        preprocessor = TextPreprocessor()
        return JobAnalyzer(skill_extractor=skill_extractor, preprocessor=preprocessor)

    @pytest.fixture
    def sample_job_description(self):
        return """Job Title: Python Developer
Company: TechCorp
Description: We are seeking a skilled Python Developer to join our backend engineering team.

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
- Understanding of microservices architecture

Required Skills: Python, Django, REST API, PostgreSQL, Git
Preferred Skills: FastAPI, Docker, AWS, Celery, Flask, Redis
Experience Required: 3 years
Education Required: B.Tech Computer Science
Location: Bangalore, Karnataka
Employment Type: Full Time"""

    # --- Section Splitting Tests ---

    def test_split_sections_basic(self, analyzer):
        """Test basic section splitting."""
        text = """Requirements:
- Python
- Django

Preferred:
- Docker
- AWS

Responsibilities:
- Build APIs
- Write tests"""

        sections = analyzer._split_sections(text)

        assert 'requirements' in sections
        assert 'preferred' in sections
        assert 'responsibilities' in sections
        assert 'python' in sections['requirements'].lower()
        assert 'docker' in sections['preferred'].lower()

    def test_split_sections_varied_headers(self, analyzer):
        """Test section splitting with various header formats."""
        text = """QUALIFICATIONS:
- Bachelor's degree
- 5 years experience

NICE TO HAVE:
- AWS certification

KEY RESPONSIBILITIES:
- Lead team
- Code review"""

        sections = analyzer._split_sections(text)

        assert 'qualifications' in sections
        assert 'nice_to_have' in sections or 'preferred' in sections
        assert 'responsibilities' in sections

    def test_split_sections_case_insensitive(self, analyzer):
        """Test section headers are case insensitive."""
        text = """requirements:
- python

PREFERRED:
- docker"""

        sections = analyzer._split_sections(text)
        assert 'requirements' in sections
        assert 'preferred' in sections

    # --- Skill Extraction Tests ---

    def test_extract_required_skills(self, analyzer, sample_job_description):
        """Test extraction of required skills from job description."""
        req = analyzer.analyze(sample_job_description)

        required_skills = set(req.required_skills)
        assert 'python' in required_skills
        assert 'django' in required_skills
        assert 'rest api' in required_skills or 'rest' in required_skills
        assert 'postgresql' in required_skills
        assert 'git' in required_skills

    def test_extract_preferred_skills(self, analyzer, sample_job_description):
        """Test extraction of preferred skills."""
        req = analyzer.analyze(sample_job_description)

        preferred_skills = set(req.preferred_skills)
        assert 'fastapi' in preferred_skills
        assert 'docker' in preferred_skills
        assert 'aws' in preferred_skills
        assert 'celery' in preferred_skills
        assert 'flask' in preferred_skills
        assert 'redis' in preferred_skills

    def test_skill_extraction_from_requirements_section(self, analyzer):
        """Test skills extracted from Requirements section."""
        text = """Requirements:
- Python
- Java
- Spring Boot

Preferred:
- Kubernetes"""

        req = analyzer.analyze(text)
        required = set(req.required_skills)
        assert 'python' in required
        assert 'java' in required
        assert 'spring boot' in required

    # --- Experience Extraction Tests ---

    def test_extract_required_experience(self, analyzer, sample_job_description):
        """Test extraction of required years of experience."""
        req = analyzer.analyze(sample_job_description)
        assert req.required_experience == 3

    def test_extract_preferred_experience(self, analyzer, sample_job_description):
        """Test extraction of preferred years of experience."""
        req = analyzer.analyze(sample_job_description)
        # Preferred experience may not be explicitly stated, should be >= required
        assert req.preferred_experience >= req.required_experience

    def test_extract_experience_various_formats(self, analyzer):
        """Test experience extraction from various formats."""
        test_cases = [
            ("Experience Required: 5 years", 5),
            ("Required: 3+ years experience", 3),
            ("Minimum 2 years", 2),
            ("At least 4 years of experience", 4),
        ]
        for text, expected in test_cases:
            req = analyzer.analyze(text)
            assert req.required_experience == expected, f"Failed for: {text}"

    # --- Education Extraction Tests ---

    def test_extract_required_education(self, analyzer, sample_job_description):
        """Test extraction of required education."""
        req = analyzer.analyze(sample_job_description)

        assert len(req.required_education) > 0
        edu_text = ' '.join(req.required_education).lower()
        assert 'b.tech' in edu_text or 'bachelor' in edu_text
        assert 'computer science' in edu_text

    def test_extract_education_various_formats(self, analyzer):
        """Test education extraction from various formats."""
        test_cases = [
            "Education Required: B.Tech Computer Science",
            "Education: Master's in Data Science",
            "Qualifications: PhD in Machine Learning",
            "Degree: Bachelor of Engineering",
        ]
        for text in test_cases:
            req = analyzer.analyze(text)
            assert len(req.required_education) > 0, f"Failed for: {text}"

    def test_extract_preferred_education(self, analyzer):
        """Test extraction of preferred education."""
        text = """Requirements:
- B.Tech

Preferred:
- Master's degree preferred"""

        req = analyzer.analyze(text)
        assert len(req.required_education) > 0
        assert len(req.preferred_education) > 0

    # --- Responsibilities Extraction Tests ---

    def test_extract_responsibilities(self, analyzer):
        """Test extraction of key responsibilities."""
        text = """Responsibilities:
- Design and develop REST APIs
- Write unit tests
- Participate in code reviews
- Collaborate with cross-functional teams"""

        req = analyzer.analyze(text)
        assert len(req.responsibilities) > 0
        resp_text = ' '.join(req.responsibilities).lower()
        assert 'api' in resp_text or 'rest' in resp_text
        assert 'test' in resp_text

    # --- Full Analysis Integration Tests ---

    def test_analyze_complete_job(self, analyzer, sample_job_description):
        """Test complete job analysis."""
        req = analyzer.analyze(sample_job_description)

        # All fields should be populated
        assert len(req.required_skills) > 0
        assert len(req.preferred_skills) > 0
        assert req.required_experience > 0
        assert len(req.required_education) > 0
        assert len(req.responsibilities) > 0

    def test_analyze_minimal_job(self, analyzer):
        """Test analysis of minimal job description."""
        text = "We need a Python developer."
        req = analyzer.analyze(text)

        # Should not crash, may have empty fields
        assert isinstance(req.required_skills, list)
        assert isinstance(req.preferred_skills, list)
        assert isinstance(req.required_education, list)
        assert isinstance(req.preferred_education, list)
        assert isinstance(req.responsibilities, list)
        assert isinstance(req.required_experience, int)
        assert isinstance(req.preferred_experience, int)

    def test_analyze_empty_job(self, analyzer):
        """Test analysis of empty job description."""
        req = analyzer.analyze("")

        assert req.required_skills == []
        assert req.preferred_skills == []
        assert req.required_education == []
        assert req.preferred_education == []
        assert req.responsibilities == []
        assert req.required_experience == 0
        assert req.preferred_experience == 0


class TestJobAnalyzerEdgeCases:
    """Edge case tests for JobAnalyzer."""

    @pytest.fixture
    def analyzer(self):
        skill_extractor = SkillExtractor()
        preprocessor = TextPreprocessor()
        return JobAnalyzer(skill_extractor=skill_extractor, preprocessor=preprocessor)

    def test_job_with_no_requirements_section(self, analyzer):
        """Test job description without explicit Requirements section."""
        text = """We are looking for a Python developer with Django experience.
        3 years experience required.
        B.Tech preferred."""

        req = analyzer.analyze(text)
        # Should still extract skills from general text
        assert 'python' in req.required_skills or 'django' in req.required_skills

    def test_job_with_bullet_points(self, analyzer):
        """Test job with bullet point formatting."""
        text = """Requirements:
• Python
• Django
• PostgreSQL

Preferred:
• Docker
• AWS"""

        req = analyzer.analyze(text)
        required = set(req.required_skills)
        assert 'python' in required
        assert 'django' in required
        assert 'postgresql' in required

    def test_job_with_numbered_list(self, analyzer):
        """Test job with numbered list."""
        text = """Requirements:
1. Python
2. Django
3. 3 years experience"""

        req = analyzer.analyze(text)
        assert 'python' in req.required_skills
        assert 'django' in req.required_skills
        assert req.required_experience == 3

    def test_skill_normalization_in_job(self, analyzer):
        """Test that skills in job description are normalized."""
        text = """Required Skills: Py, JS, ML, AI, AWS"""
        req = analyzer.analyze(text)

        skills = set(req.required_skills)
        assert 'python' in skills
        assert 'javascript' in skills
        assert 'machine learning' in skills or 'ml' in skills


if __name__ == '__main__':
    pytest.main([__file__, '-v'])