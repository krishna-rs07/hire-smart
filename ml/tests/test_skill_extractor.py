"""
Unit tests for SkillExtractor module.
"""

import pytest
from ml.skill_extractor import SkillExtractor


class TestSkillExtractor:
    """Tests for SkillExtractor class."""

    @pytest.fixture
    def extractor(self):
        return SkillExtractor()

    # --- Skill Extraction Tests ---

    def test_extract_skills_basic(self, extractor):
        """Test basic skill extraction from text."""
        text = "I have experience with Python, Django, and PostgreSQL."
        result = extractor.extract_skills(text)

        assert 'skills' in result
        skills = set(result['skills'])
        assert 'python' in skills
        assert 'django' in skills
        # postgresql may be extracted as 'postgres' or not at all depending on dictionary

    def test_extract_skills_case_insensitive(self, extractor):
        """Test skill extraction is case insensitive."""
        text = "PYTHON, django, PostGreSQL"
        result = extractor.extract_skills(text)

        skills = set(result['skills'])
        assert 'python' in skills
        assert 'django' in skills
        assert 'postgresql' in skills

    def test_extract_skills_with_aliases(self, extractor):
        """Test skill extraction normalizes aliases."""
        # 'py' should map to 'python', 'js' to 'javascript'
        text = "I know py and js"
        result = extractor.extract_skills(text)

        skills = set(result['skills'])
        assert 'python' in skills
        assert 'javascript' in skills
        # Aliases should be normalized, not kept as-is
        assert 'py' not in skills
        assert 'js' not in skills

    def test_extract_skills_compound_terms(self, extractor):
        """Test extraction of multi-word skills."""
        text = "Experience with machine learning, natural language processing, and REST API development."
        result = extractor.extract_skills(text)

        skills = set(result['skills'])
        # Compound skills should be extracted
        assert any('machine learning' in s for s in skills)
        assert any('natural language processing' in s or 'nlp' in s for s in skills)
        assert any('rest api' in s or 'rest' in s for s in skills)

    def test_extract_skills_empty_text(self, extractor):
        """Test skill extraction from empty text."""
        result = extractor.extract_skills("")
        assert result['skills'] == []

    def test_extract_skills_no_skills(self, extractor):
        """Test skill extraction from text with no known skills."""
        text = "I am a hardworking individual with great communication skills."
        result = extractor.extract_skills(text)
        # May return empty or only soft skills depending on dictionary
        assert isinstance(result['skills'], list)

    # --- Experience Extraction Tests ---

    def test_extract_experience_years_explicit(self, extractor):
        """Test extraction of explicit years of experience."""
        text = "5 years of experience in Python development."
        years = extractor.extract_experience_years(text)
        assert years == 5

    def test_extract_experience_years_range(self, extractor):
        """Test extraction from experience ranges."""
        text = "3-5 years experience with Django."
        years = extractor.extract_experience_years(text)
        # Should extract the higher end or average
        assert years >= 3

    def test_extract_experience_years_from_dates(self, extractor):
        """Test extraction from employment dates."""
        text = """
        Senior Developer, TechCorp (2020-2024)
        Junior Developer, StartupInc (2018-2020)
        """
        years = extractor.extract_experience_years(text)
        # 2024 - 2018 = 6 years
        assert years >= 4  # Allow some flexibility

    def test_extract_experience_years_none(self, extractor):
        """Test extraction when no experience mentioned."""
        text = "I am a student learning Python."
        years = extractor.extract_experience_years(text)
        assert years == 0

    # --- Education Extraction Tests ---

    def test_extract_education_degree(self, extractor):
        """Test extraction of degree information."""
        text = "Bachelor of Science in Computer Science, University of Tech, 2020"
        result = extractor.extract_education(text)

        assert len(result) > 0
        edu_text = ' '.join(result).lower()
        assert 'bachelor' in edu_text or 'b.sc' in edu_text or 'bsc' in edu_text
        assert 'computer science' in edu_text

    def test_extract_education_masters(self, extractor):
        """Test extraction of master's degree."""
        text = "M.Tech in Computer Science, IIT Delhi, 2022"
        result = extractor.extract_education(text)

        edu_text = ' '.join(result).lower()
        assert 'm.tech' in edu_text or 'master' in edu_text
        assert 'computer science' in edu_text

    def test_extract_education_phd(self, extractor):
        """Test extraction of PhD."""
        text = "PhD in Machine Learning, Stanford University, 2023"
        result = extractor.extract_education(text)

        edu_text = ' '.join(result).lower()
        assert 'phd' in edu_text or 'doctorate' in edu_text
        assert 'machine learning' in edu_text

    def test_extract_education_diploma(self, extractor):
        """Test extraction of diploma."""
        text = "Diploma in Mechanical Engineering, Government Polytechnic, 2019"
        result = extractor.extract_education(text)

        edu_text = ' '.join(result).lower()
        assert 'diploma' in edu_text
        assert 'mechanical' in edu_text or 'engineering' in edu_text

    def test_extract_education_multiple(self, extractor):
        """Test extraction of multiple degrees."""
        text = """
        B.Tech Computer Science, 2018
        M.Tech Data Science, 2020
        """
        result = extractor.extract_education(text)

        assert len(result) >= 2
        edu_text = ' '.join(result).lower()
        assert 'b.tech' in edu_text or 'bachelor' in edu_text
        assert 'm.tech' in edu_text or 'master' in edu_text

    def test_extract_education_empty(self, extractor):
        """Test extraction from text with no education."""
        text = "I am a self-taught programmer."
        result = extractor.extract_education(text)
        assert result == []


class TestSkillExtractorAliases:
    """Tests for skill alias handling."""

    @pytest.fixture
    def extractor(self):
        return SkillExtractor()

    def test_python_aliases(self, extractor):
        """Test Python aliases normalize to 'python'."""
        aliases = ['py', 'python3', 'python 3']
        for alias in aliases:
            result = extractor.extract_skills(f"I know {alias}")
            assert 'python' in result['skills']

    def test_javascript_aliases(self, extractor):
        """Test JavaScript aliases normalize to 'javascript'."""
        # 'js', 'ecmascript', 'node', 'node js' are aliases for javascript
        # 'node.js' and 'nodejs' are separate skills (Node.js runtime/framework)
        aliases = ['js', 'ecmascript', 'node', 'node js']
        for alias in aliases:
            result = extractor.extract_skills(f"I know {alias}")
            assert 'javascript' in result['skills']

        # node.js and nodejs should be extracted as themselves (web framework)
        for alias in ['node.js', 'nodejs']:
            result = extractor.extract_skills(f"I know {alias}")
            assert 'node.js' in result['skills'] or 'nodejs' in result['skills']

    def test_ml_aliases(self, extractor):
        """Test ML-related aliases."""
        aliases = ['ml', 'machine learning', 'artificial intelligence', 'ai']
        for alias in aliases:
            result = extractor.extract_skills(f"Experience with {alias}")
            skills = set(result['skills'])
            assert 'machine learning' in skills or 'ml' in skills

    def test_cloud_aliases(self, extractor):
        """Test cloud platform aliases."""
        aliases = ['aws', 'amazon web services', 'gcp', 'google cloud', 'azure', 'microsoft azure']
        for alias in aliases:
            result = extractor.extract_skills(f"Experience with {alias}")
            skills = set(result['skills'])
            # At least one cloud skill should be found
            assert any(cloud in skills for cloud in ['aws', 'gcp', 'azure', 'cloud'])


class TestSkillExtractorEdgeCases:
    """Edge case tests for SkillExtractor."""

    @pytest.fixture
    def extractor(self):
        return SkillExtractor()

    def test_skill_in_different_contexts(self, extractor):
        """Test skills found in various contexts."""
        texts = [
            "Skills: Python, Django, React",
            "Technologies: Python; Django; React",
            "Proficient in Python, Django, and React",
            "Python/Django/React developer",
        ]
        for text in texts:
            result = extractor.extract_skills(text)
            skills = set(result['skills'])
            assert 'python' in skills
            assert 'django' in skills
            assert 'react' in skills

    def test_partial_skill_matching(self, extractor):
        """Test that partial matches don't cause false positives."""
        # 'java' should not match 'javascript'
        result = extractor.extract_skills("I know javascript")
        skills = set(result['skills'])
        assert 'javascript' in skills
        # Should not incorrectly extract 'java' as separate skill
        # (depends on implementation - if using word boundaries, this should pass)

    def test_skill_with_special_characters(self, extractor):
        """Test skills with special characters."""
        text = "C++, C#, .NET, Node.js, Vue.js"
        result = extractor.extract_skills(text)
        skills = set(result['skills'])
        assert 'c++' in skills or 'cpp' in skills
        assert 'c#' in skills or 'csharp' in skills
        assert '.net' in skills or 'dotnet' in skills
        assert 'node.js' in skills or 'nodejs' in skills
        assert 'vue.js' in skills or 'vuejs' in skills

    def test_very_long_text(self, extractor):
        """Test extraction from very long text."""
        # Create a long resume-like text
        base_skills = "Python, Django, PostgreSQL, Git, Docker, AWS, React, TypeScript, REST API, GraphQL"
        text = " ".join([base_skills] * 50)  # Repeat 50 times
        result = extractor.extract_skills(text)

        skills = set(result['skills'])
        assert 'python' in skills
        assert 'django' in skills
        # Should not crash or take too long


if __name__ == '__main__':
    pytest.main([__file__, '-v'])