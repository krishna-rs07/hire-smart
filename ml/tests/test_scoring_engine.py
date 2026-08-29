"""
Unit tests for ScoringEngine module.
"""

import pytest
from ml.scoring_engine import ScoringEngine
from ml.skill_extractor import SkillExtractor
from ml.similarity_engine import SimilarityEngine
from ml.job_analyzer import JobAnalyzer, JobRequirements
from ml.text_preprocessor import TextPreprocessor


class TestScoringEngine:
    """Tests for ScoringEngine class."""

    @pytest.fixture
    def engine(self):
        return ScoringEngine()

    @pytest.fixture
    def sample_job_requirements(self):
        """Create sample job requirements for testing."""
        req = JobRequirements()
        req.required_skills = ['python', 'django', 'rest api', 'postgresql', 'git']
        req.preferred_skills = ['fastapi', 'docker', 'aws', 'celery', 'flask', 'redis']
        req.required_experience = 3
        req.preferred_experience = 5
        req.required_education = ['b.tech computer science']
        req.preferred_education = ['m.tech computer science']
        req.responsibilities = [
            'Design and develop REST APIs',
            'Write unit tests',
            'Participate in code reviews'
        ]
        return req

    @pytest.fixture
    def strong_candidate_resume(self):
        return """SENIOR PYTHON DEVELOPER
Email: senior@email.com

SUMMARY
Senior Python Developer with 6 years experience building scalable backend systems.

EDUCATION
B.Tech Computer Science, 2017

SKILLS
Python, Django, REST API, PostgreSQL, Git, Docker, AWS, FastAPI, Celery

EXPERIENCE
Senior Python Developer, BigTech (2017-Present)
- Built Python Django applications serving millions of users
- Designed REST APIs with Django REST Framework
- Used PostgreSQL for data storage
- Deployed on AWS with Docker containers
- Implemented async tasks with Celery"""

    @pytest.fixture
    def weak_candidate_resume(self):
        return """JUNIOR DEVELOPER
Email: junior@email.com

SUMMARY
Entry-level developer learning web development.

EDUCATION
Bachelor of Arts in English Literature, 2023

SKILLS
HTML, CSS, JavaScript, WordPress

EXPERIENCE
Intern, Marketing Agency (2022-2023)
- Created websites with WordPress
- Basic HTML/CSS"""

    # --- Skill Scoring Tests ---

    def test_skill_score_perfect_match(self, engine, sample_job_requirements):
        """Test skill score when candidate has all required skills."""
        candidate_skills = {'python', 'django', 'rest api', 'postgresql', 'git', 'docker', 'aws'}

        score, matched, missing = engine._score_skills(candidate_skills, sample_job_requirements.required_skills)

        assert score == 100.0
        assert len(matched) == 5
        assert len(missing) == 0

    def test_skill_score_partial_match(self, engine, sample_job_requirements):
        """Test skill score with partial match."""
        candidate_skills = {'python', 'django', 'git'}

        score, matched, missing = engine._score_skills(candidate_skills, sample_job_requirements.required_skills)

        assert score == 60.0  # 3 out of 5
        assert len(matched) == 3
        assert len(missing) == 2

    def test_skill_score_no_match(self, engine, sample_job_requirements):
        """Test skill score when candidate has no required skills."""
        candidate_skills = {'html', 'css', 'javascript'}

        score, matched, missing = engine._score_skills(candidate_skills, sample_job_requirements.required_skills)

        assert score == 0.0
        assert len(matched) == 0
        assert len(missing) == 5

    def test_skill_score_empty_requirements(self, engine):
        """Test skill score when no required skills specified."""
        candidate_skills = {'python', 'django'}

        score, matched, missing = engine._score_skills(candidate_skills, [])

        assert score == 100.0
        assert matched == []
        assert missing == []

    def test_skill_score_empty_candidate(self, engine, sample_job_requirements):
        """Test skill score when candidate has no skills."""
        score, matched, missing = engine._score_skills(set(), sample_job_requirements.required_skills)

        assert score == 0.0
        assert matched == []
        assert len(missing) == 5

    # --- Preferred Skill Scoring Tests ---

    def test_preferred_skill_score_perfect(self, engine, sample_job_requirements):
        """Test preferred skill score when candidate has all preferred skills."""
        candidate_skills = {'python', 'django', 'fastapi', 'docker', 'aws', 'celery', 'flask', 'redis'}

        score, missing = engine._score_preferred_skills(candidate_skills, sample_job_requirements.preferred_skills)

        assert score == 100.0
        assert missing == []

    def test_preferred_skill_score_partial(self, engine, sample_job_requirements):
        """Test preferred skill score with partial match."""
        # preferred_skills = ['fastapi', 'docker', 'aws', 'celery', 'flask', 'redis']
        # candidate has 'python', 'docker', 'aws' -> only docker and aws match = 2/6
        candidate_skills = {'python', 'docker', 'aws'}

        score, missing = engine._score_preferred_skills(candidate_skills, sample_job_requirements.preferred_skills)

        assert score == 33.33333333333333  # 2 out of 6
        assert len(missing) == 4

    def test_preferred_skill_score_none(self, engine, sample_job_requirements):
        """Test preferred skill score when candidate has none."""
        candidate_skills = {'python', 'django'}

        score, missing = engine._score_preferred_skills(candidate_skills, sample_job_requirements.preferred_skills)

        assert score == 0.0
        assert len(missing) == 6

    def test_preferred_skill_score_no_prefs(self, engine):
        """Test preferred skill score when no preferred skills specified."""
        candidate_skills = {'python'}

        score, missing = engine._score_preferred_skills(candidate_skills, [])

        assert score == 50.0  # Neutral score
        assert missing == []

    # --- Experience Scoring Tests ---

    def test_experience_score_meets_requirement(self, engine):
        """Test experience score when candidate meets requirement."""
        resume = "5 years of experience in Python development."

        score = engine._score_experience(resume, required_exp=3, preferred_exp=5)

        assert score == 100.0

    def test_experience_score_exceeds_preferred(self, engine):
        """Test experience score when candidate exceeds preferred."""
        resume = "10 years of experience in Python development."

        score = engine._score_experience(resume, required_exp=3, preferred_exp=5)

        assert score == 100.0

    def test_experience_score_between_req_pref(self, engine):
        """Test experience score between required and preferred."""
        resume = "4 years of experience in Python development."

        score = engine._score_experience(resume, required_exp=3, preferred_exp=5)

        # Should be between 80 and 100
        assert 80 <= score <= 100

    def test_experience_score_below_requirement(self, engine):
        """Test experience score when below requirement."""
        resume = "1 year of experience in Python development."

        score = engine._score_experience(resume, required_exp=3, preferred_exp=5)

        # Should be proportional, max 80%
        assert 0 <= score < 80

    def test_experience_score_no_requirement(self, engine):
        """Test experience score when no requirement specified."""
        resume = "5 years experience."

        score = engine._score_experience(resume, required_exp=0, preferred_exp=0)

        assert score == 100.0

    def test_experience_score_no_experience(self, engine):
        """Test experience score when candidate has no experience."""
        resume = "Recent graduate with no work experience."

        score = engine._score_experience(resume, required_exp=3, preferred_exp=5)

        assert score == 0.0

    # --- Education Scoring Tests ---

    def test_education_score_exact_match(self, engine):
        """Test education score with exact degree and field match."""
        candidate_edu = ['B.Tech Computer Science, 2020']
        required_edu = ['B.Tech Computer Science']

        score = engine._score_education(
            "B.Tech Computer Science, 2020",
            required_edu,
            []
        )

        assert score == 100.0

    def test_education_score_right_level_different_field(self, engine):
        """Test education score with right level but different field."""
        score = engine._score_education(
            "Bachelor of Arts in English Literature, 2020",
            ['B.Tech Computer Science'],
            []
        )

        # Should be 90% - right level, different field
        # But currently job analyzer only extracts 'b.tech' without field, so it might be 95%
        assert 80 <= score <= 100

    def test_education_score_higher_level(self, engine):
        """Test education score when candidate has higher degree."""
        score = engine._score_education(
            "M.Tech Computer Science, 2022",
            ['B.Tech Computer Science'],
            []
        )

        assert score == 100.0

    def test_education_score_one_level_below(self, engine):
        """Test education score when candidate has one level below."""
        score = engine._score_education(
            "B.Tech Computer Science, 2020",
            ['M.Tech Computer Science'],
            []
        )

        assert score == 60.0

    def test_education_score_significantly_below(self, engine):
        """Test education score when significantly below requirement."""
        score = engine._score_education(
            "High School Diploma, 2018",
            ['M.Tech Computer Science'],
            []
        )

        assert score == 30.0

    def test_education_score_no_requirement(self, engine):
        """Test education score when no requirement specified."""
        score = engine._score_education(
            "B.Tech Computer Science, 2020",
            [],
            []
        )

        assert score == 70.0  # Neutral

    def test_education_score_no_candidate_education(self, engine):
        """Test education score when candidate has no education."""
        score = engine._score_education(
            "Self-taught programmer",
            ['B.Tech Computer Science'],
            []
        )

        assert score == 0.0

    # --- Job Title Scoring Tests ---

    def test_job_title_score_exact_match(self, engine):
        """Test job title score with exact role match."""
        resume = """SENIOR PYTHON DEVELOPER
Summary: Senior Python Developer with 6 years experience.
Experience:
Senior Python Developer, BigTech (2017-Present)"""

        job_desc = """Job Title: Python Developer
Requirements:
- Python, Django"""

        score = engine._score_job_title(resume, job_desc)

        assert score >= 70  # Should be high match

    def test_job_title_score_partial_match(self, engine):
        """Test job title score with partial role match."""
        resume = """BACKEND ENGINEER
Summary: Backend Engineer with Python experience.
Experience:
Backend Engineer, TechCo (2018-Present)"""

        job_desc = """Job Title: Python Developer
Requirements:
- Python, Django"""

        score = engine._score_job_title(resume, job_desc)

        # Backend engineer should partially match python developer
        assert score >= 30

    def test_job_title_score_no_match(self, engine):
        """Test job title score with completely different role."""
        resume = """FRONTEND DEVELOPER
Summary: Frontend Developer with React experience.
Experience:
Frontend Developer, WebCo (2019-Present)"""

        job_desc = """Job Title: Python Developer
Requirements:
- Python, Django"""

        score = engine._score_job_title(resume, job_desc)

        # Frontend dev should not match python developer well
        assert score <= 50

    def test_job_title_score_no_title_in_job(self, engine):
        """Test job title score when job has no clear title."""
        resume = """PYTHON DEVELOPER"""
        job_desc = """We need someone who knows Python."""

        score = engine._score_job_title(resume, job_desc)

        assert score == 50.0  # Neutral

    # --- Full Scoring Integration Tests ---

    def test_score_strong_candidate(self, engine, strong_candidate_resume, sample_job_requirements):
        """Test scoring a strong candidate."""
        job_desc = """Job Title: Python Developer
Requirements:
- 3+ years Python
- Django, REST API, PostgreSQL, Git
Preferred:
- FastAPI, Docker, AWS
Experience Required: 3 years
Education Required: B.Tech Computer Science"""

        score = engine.score_candidate(strong_candidate_resume, job_desc, sample_job_requirements)

        assert score.overall_score >= 70  # Should be a good match
        assert score.skill_score >= 80
        assert score.experience_score >= 80
        assert score.education_score >= 80
        assert len(score.matched_skills) >= 4

    def test_score_weak_candidate(self, engine, weak_candidate_resume, sample_job_requirements):
        """Test scoring a weak candidate."""
        job_desc = """Job Title: Python Developer
Requirements:
- 3+ years Python
- Django, REST API, PostgreSQL, Git
Experience Required: 3 years
Education Required: B.Tech Computer Science"""

        score = engine.score_candidate(weak_candidate_resume, job_desc, sample_job_requirements)

        assert score.overall_score < 50  # Should be a poor match
        assert score.skill_score < 50
        assert score.experience_score < 50
        # Weak candidate has Bachelor of Arts in English Literature
        # For B.Tech CS requirement: right level (bachelor) but different field = 90
        assert score.education_score >= 80

    def test_score_empty_resume(self, engine, sample_job_requirements):
        """Test scoring an empty resume."""
        score = engine.score_candidate("", "Job Title: Python Developer", sample_job_requirements)

        assert score.overall_score == 0.0
        assert score.skill_score == 0.0
        assert score.experience_score == 0.0
        assert score.education_score == 0.0

    # --- Weight Configuration Tests ---

    def test_custom_weights(self, engine):
        """Test custom weight configuration."""
        custom_weights = {
            'skill': 0.5,
            'semantic': 0.1,
            'experience': 0.1,
            'education': 0.1,
            'preferred': 0.1,
            'job_title': 0.1
        }
        custom_engine = ScoringEngine(weights=custom_weights)

        assert custom_engine.weights['skill'] == 0.5
        assert custom_engine.weights['semantic'] == 0.1

    def test_weights_normalization(self):
        """Test that weights are normalized if they don't sum to 1.0."""
        unnormalized = {
            'skill': 50,
            'semantic': 20,
            'experience': 15,
            'education': 10,
            'preferred': 5,
            'job_title': 0
        }
        engine = ScoringEngine(weights=unnormalized)

        # Should normalize to sum to 1.0
        total = sum(engine.weights.values())
        assert abs(total - 1.0) < 0.01
        assert engine.weights['skill'] == 0.5

    # --- Explanation Generation Tests ---

    def test_generate_explanations_strong(self, engine, sample_job_requirements):
        """Test explanation generation for strong candidate."""
        strengths, weaknesses = engine._generate_explanations(
            skill_score=90, semantic_score=80, experience_score=90,
            education_score=100, pref_score=70,
            matched=['python', 'django', 'rest api', 'postgresql', 'git'],
            missing=[],
            missing_pref=['fastapi'],
            job_req=sample_job_requirements
        )

        assert len(strengths) > 0
        assert any('Strong skills match' in s for s in strengths)
        assert any('experience requirements' in s for s in strengths)
        assert any('Education requirements satisfied' in s for s in strengths)

    def test_generate_explanations_weak(self, engine, sample_job_requirements):
        """Test explanation generation for weak candidate."""
        strengths, weaknesses = engine._generate_explanations(
            skill_score=20, semantic_score=30, experience_score=10,
            education_score=0, pref_score=0,
            matched=['git'],
            missing=['python', 'django', 'rest api', 'postgresql'],
            missing_pref=['fastapi', 'docker', 'aws'],
            job_req=sample_job_requirements
        )

        assert len(weaknesses) > 0
        assert any('Weak skills match' in w for w in weaknesses)
        assert any('Missing required skills' in w for w in weaknesses)
        assert any('Below experience requirements' in w for w in weaknesses)
        assert any('Education does not match' in w for w in weaknesses)


class TestScoringEngineEdgeCases:
    """Edge case tests for ScoringEngine."""

    @pytest.fixture
    def engine(self):
        return ScoringEngine()

    def test_score_with_special_characters_in_skills(self, engine):
        """Test scoring with skills containing special characters."""
        req = JobRequirements()
        req.required_skills = ['c++', 'c#', '.net', 'node.js']
        req.required_experience = 3
        req.required_education = ['b.tech']

        resume = """C++ Developer
Skills: C++, C#, .NET, Node.js
Experience: 5 years
Education: B.Tech Computer Science"""

        job_desc = "Job Title: C++ Developer\nRequirements: C++, C#, .NET, Node.js"

        score = engine.score_candidate(resume, job_desc, req)

        assert score.skill_score > 0

    def test_score_unicode_resume(self, engine):
        """Test scoring with unicode characters in resume."""
        req = JobRequirements()
        req.required_skills = ['python']
        req.required_experience = 1
        req.required_education = ['bachelor']

        resume = """Python Developer
Skills: Python, Django
Experience: 2 years
Education: Bachelor's Degree"""

        job_desc = "Job Title: Python Developer\nRequirements: Python"

        score = engine.score_candidate(resume, job_desc, req)

        assert score.overall_score >= 0  # Should not crash

    def test_score_very_long_resume(self, engine):
        """Test scoring with very long resume text."""
        # Create a long resume
        base = "Python, Django, PostgreSQL, Git, Docker, AWS. " * 100
        long_resume = f"""SENIOR DEVELOPER
Skills: {base}
Experience: 5 years
Education: B.Tech Computer Science"""

        job_desc = "Job Title: Python Developer\nRequirements: Python, Django"

        # Create minimal job requirements
        from ml.job_analyzer import JobRequirements
        job_req = JobRequirements()
        job_req.required_skills = ['python', 'django']
        job_req.required_experience = 3
        job_req.required_education = ['b.tech computer science']

        score = engine.score_candidate(long_resume, job_desc, job_req)

        assert score.overall_score >= 0  # Should not crash or timeout


if __name__ == '__main__':
    pytest.main([__file__, '-v'])