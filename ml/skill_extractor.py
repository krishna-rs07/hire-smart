"""
Skill Extractor Module
Extracts skills from resume text using a configurable skill dictionary and pattern matching.
"""

import re
import json
import logging
from typing import List, Dict, Set, Optional
from pathlib import Path

from .text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)


class SkillExtractor:
    """
    Extract technical and soft skills from resume text.

    Uses a configurable skill dictionary organized by category with
    alias mapping for different ways skills can be written.
    """

    # Default skill dictionary - organized by category with common aliases
    DEFAULT_SKILLS = {
        'programming_languages': [
            'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'c', 'php', 'ruby',
            'go', 'rust', 'swift', 'kotlin', 'scala', 'r', 'matlab', 'perl', 'shell', 'bash',
            'powershell', 'sql', 'html', 'css', 'sass', 'less', 'dart', 'objective-c', 'groovy',
            'ecmascript'
        ],
        'web_frameworks': [
            'django', 'flask', 'fastapi', 'react', 'react.js', 'angular', 'vue', 'vue.js', 'node.js', 'nodejs',
            'express.js', 'express', 'spring', 'spring boot', 'laravel', 'rails', 'asp.net',
            'dotnet', 'next.js', 'nuxt', 'gatsby', 'svelte', 'bootstrap', 'tailwind', 'jquery',
            'redux', 'graphql', 'rest api', 'restful', 'webpack', 'vite', 'symfony', 'codeigniter',
            'celery', 'gunicorn', 'uvicorn', 'daphne', 'asgi', 'wsgi'
        ],
        'databases': [
            'mysql', 'postgresql', 'postgres', 'mongodb', 'redis', 'sqlite', 'oracle', 'sql server',
            'sqlserver', 'cassandra', 'dynamodb', 'elasticsearch', 'neo4j', 'firebase', 'mariadb',
            'cockroachdb', 'bigquery', 'snowflake', 'redshift'
        ],
        'cloud_devops': [
            'aws', 'azure', 'gcp', 'google cloud', 'google cloud platform', 'docker', 'kubernetes', 'k8s', 'terraform',
            'ansible', 'jenkins', 'gitlab ci', 'github actions', 'circleci', 'travis', 'helm',
            'prometheus', 'grafana', 'nginx', 'apache', 'linux', 'unix', 'centos', 'ubuntu',
            'serverless', 'lambda', 'ec2', 's3', 'cloudformation', 'vagrant', 'puppet', 'chef',
            'amazon web services', 'microsoft azure', 'amazon web services', 'google cloud platform'
        ],
        'data_ml': [
            'machine learning', 'deep learning', 'tensorflow', 'keras', 'pytorch', 'scikit-learn',
            'sklearn', 'pandas', 'numpy', 'scipy', 'matplotlib', 'seaborn', 'nlp', 'natural language',
            'computer vision', 'opencv', 'xgboost', 'lightgbm', 'spark', 'hadoop', 'pyspark',
            'data science', 'data analysis', 'statistics', 'tableau', 'power bi', 'looker',
            'feature engineering', 'model deployment', 'mlops', 'databricks', 'airflow',
            'artificial intelligence', 'computer vision', 'data engineering', 'etl'
        ],
        'tools_technologies': [
            'git', 'github', 'gitlab', 'bitbucket', 'jira', 'confluence', 'slack', 'trello',
            'postman', 'swagger', 'junit', 'pytest', 'selenium', 'cypress', 'jmeter', 'figma',
            'adobe xd', 'photoshop', 'illustrator', 'sketch', 'invision', 'balsamiq'
        ],
        'methodologies': [
            'agile', 'scrum', 'kanban', 'waterfall', 'devops', 'ci/cd', 'cicd', 'tdd', 'test driven',
            'microservices', 'monolithic', 'rest', 'soap', 'mvvm', 'mvc', 'design patterns',
            'solid', 'object oriented', 'oop', 'functional programming'
        ],
        'soft_skills': [
            'communication', 'leadership', 'teamwork', 'problem solving', 'critical thinking',
            'creativity', 'adaptability', 'time management', 'collaboration', 'presentation',
            'negotiation', 'project management', 'stakeholder management', 'mentoring', 'coaching'
        ],
        'business_domain': [
            'finance', 'healthcare', 'e-commerce', 'retail', 'banking', 'insurance', 'telecom',
            'manufacturing', 'fintech', 'edtech', 'saas', 'b2b', 'b2c', 'marketing', 'sales',
            'hr', 'human resources', 'supply chain', 'logistics', 'real estate'
        ]
    }

    # Alias mapping - different ways skills can be written
    # Keys must be skills present in skills_dict (or will be added)
    DEFAULT_ALIASES = {
        'javascript': ['js', 'ecmascript', 'node', 'node js'],
        'typescript': ['ts'],
        'python': ['py', 'python3'],
        'c++': ['cpp', 'c plus plus'],
        'c#': ['c sharp', 'csharp'],
        'postgresql': ['postgres', 'pg'],
        'sql server': ['mssql', 'ms sql'],
        'aws': ['amazon web services'],
        'gcp': ['google cloud platform', 'google cloud'],
        'azure': ['microsoft azure'],
        'kubernetes': ['k8s'],
        'ci/cd': ['cicd', 'ci cd', 'continuous integration', 'continuous integration/continuous deployment'],
        'machine learning': ['ml', 'artificial intelligence', 'ai', 'deep learning'],
        'nlp': ['natural language processing'],
        'react': ['react.js', 'reactjs', 'react js'],
        'vue.js': ['vue', 'vuejs', 'vue js'],
        'express.js': ['express', 'expressjs', 'express js'],
        'spring boot': ['spring'],
        'dotnet': ['.net', 'dot net', 'asp.net'],
        'scikit-learn': ['sklearn', 'scikit learn'],
        'rest api': ['restful', 'restful api', 'rest'],
        'oop': ['object oriented', 'object oriented programming'],
        'tdd': ['test driven development'],
        'agile': ['agile methodology', 'scrum'],
    }

    def __init__(self, custom_skills: Optional[Dict[str, List[str]]] = None,
                 custom_aliases: Optional[Dict[str, List[str]]] = None):
        """
        Initialize the skill extractor.

        Args:
            custom_skills: Additional skill categories/dictionary
            custom_aliases: Additional alias mappings
        """
        self.skills_dict = self.DEFAULT_SKILLS.copy()
        if custom_skills:
            for category, skills in custom_skills.items():
                if category in self.skills_dict:
                    self.skills_dict[category].extend(skills)
                else:
                    self.skills_dict[category] = skills

        self.aliases = self.DEFAULT_ALIASES.copy()
        if custom_aliases:
            self.aliases.update(custom_aliases)

        # Precompute flattened skill list and all aliases
        self._all_skills = set()
        for skills in self.skills_dict.values():
            self._all_skills.update(skill.lower() for skill in skills)

        # Build reverse alias lookup
        self._reverse_aliases = {}
        for canonical, aliases in self.aliases.items():
            self._reverse_aliases[canonical.lower()] = canonical.lower()
            for alias in aliases:
                self._reverse_aliases[alias.lower()] = canonical.lower()

        # Precompile patterns for efficiency
        self._compile_patterns()

    def _compile_patterns(self):
        """Compile regex patterns for skill detection."""
        # Include both skills from dict AND alias values as matchable terms
        match_terms = set(self._all_skills)
        for canonical, aliases in self.aliases.items():
            match_terms.add(canonical.lower())
            for alias in aliases:
                match_terms.add(alias.lower())

        # Sort by length (longest first) to avoid partial matches
        all_terms = sorted(match_terms, key=len, reverse=True)

        # Build pattern with word boundaries
        # Lookahead excludes word chars/dash/plus/hash but NOT trailing dot
        # (trailing dot = end of sentence like "PostgreSQL.")
        # Lookbehind excludes trailing-dot to avoid matching ".net" inside domains
        pattern_parts = []
        for term in all_terms:
            escaped = re.escape(term)
            # (?<![\w\-\+\#\.]) ... term ... (?![\w\-\+\#])
            pattern = r'(?<![\w\-\+\#\.])' + escaped + r'(?![\w\-\+\#])'
            pattern_parts.append(pattern)

        self._skill_pattern = re.compile('|'.join(pattern_parts), re.IGNORECASE)

    def extract_skills(self, text: str, include_categories: bool = True) -> Dict:
        """
        Extract skills from resume text.

        Args:
            text: Resume text
            include_categories: Whether to return categorized results

        Returns:
            Dictionary with 'skills' (list) and optionally 'categories' (dict)
        """
        if not text or not text.strip():
            return {'skills': [], 'categories': {}} if include_categories else {'skills': []}

        # Find all matches
        matches = self._skill_pattern.findall(text.lower())

        # Normalize via aliases
        normalized_skills = set()
        for match in matches:
            canonical = self._reverse_aliases.get(match.lower(), match.lower())
            normalized_skills.add(canonical)

        # Categorize
        categorized = {}
        if include_categories:
            for category, skills in self.skills_dict.items():
                category_skills = [skill for skill in skills
                                  if skill.lower() in normalized_skills]
                if category_skills:
                    categorized[category] = category_skills

        result = {
            'skills': sorted(normalized_skills),
            'categories': categorized if include_categories else {}
        }

        return result

    def extract_experience_years(self, text: str) -> int:
        """
        Extract total years of experience from resume text.

        Args:
            text: Resume text

        Returns:
            Estimated total years of experience (max found)
        """
        # Patterns for experience
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
            r'(\d+)\+?\s*yrs?\s*(?:of\s*)?(?:experience|exp)',
            r'experience\s*(?:of\s*)?(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s*in\s*(?:the\s*)?(?:field|industry)',
            # Additional patterns for "X years [technology/role]" format
            r'(\d+)\+?\s*years?\s+(?:python|django|java|javascript|development|programming|software|web|backend|frontend|full.?stack|devops|data|ml|ai)',
            r'(\d+)\+?\s*years?\s+(?:with|using|experience with)',
        ]

        max_years = 0
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            for match in matches:
                years = int(match)
                if 0 < years <= 50:  # Sanity check
                    max_years = max(max_years, years)

        # Also try to extract from employment date ranges
        # Pattern: "Company (YYYY-YYYY)" or "Company (YYYY - Present)"
        date_patterns = [
            r'\((\d{4})\s*[-–]\s*(\d{4}|present)\)',  # (2020-2024) or (2020 - present)
            r'(\d{4})\s*[-–]\s*(\d{4}|present)',      # 2020-2024 or 2020 - present
        ]

        current_year = 2024  # Use a reasonable current year
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                start_year = int(match[0])
                end_year = match[1].lower()
                if end_year in ('present', 'current'):
                    end_year = current_year
                else:
                    end_year = int(end_year)
                years = end_year - start_year
                if 0 < years <= 50:
                    max_years = max(max_years, years)

        return max_years

    def extract_education(self, text: str) -> List[str]:
        """
        Extract education information from resume text.

        Args:
            text: Resume text

        Returns:
            List of education-related strings
        """
        # Use non-capturing groups (?:...) so findall returns full matches
        degree_patterns = [
            # Full degree names with field: "Bachelor of Science in Computer Science", "PhD in Machine Learning", "Diploma in Mechanical Engineering"
            r'(?:bachelor(?:\'s)?|master(?:\'s)?|phd|doctorate|diploma|associate)\s+(?:of\s+|in\s+)?(?:science|arts|engineering|technology|business|computer\s+science|information\s+technology|data\s+science|machine\s+learning|artificial\s+intelligence|deep\s+learning|computer\s+vision|natural\s+language\s+processing|mechanical\s+engineering|electrical\s+engineering|civil\s+engineering|chemical\s+engineering|aerospace\s+engineering|industrial\s+engineering)',
            # "Bachelor of Science in Computer Science" - compound form with "of X in Y"
            r'(?:bachelor(?:\'s)?|master(?:\'s)?)\s+of\s+(?:science|arts|engineering)\s+in\s+(?:computer\s+science|engineering|information\s+technology|data\s+science|machine\s+learning|artificial\s+intelligence|deep\s+learning|computer\s+vision|natural\s+language\s+processing|mechanical\s+engineering|electrical\s+engineering|civil\s+engineering|chemical\s+engineering|aerospace\s+engineering|industrial\s+engineering|business|finance|technology|mathematics|statistics|physics|chemistry|biology|economics)',
            # Abbreviated degrees with field: "B.Tech Computer Science", "M.Tech in Data Science"
            # Allow flexible whitespace between degree and field
            r'\b(?:b\.?tech|b\.?e|m\.?tech|m\.?e|b\.?sc|m\.?sc|bsc|msc|bca|mca|bba|mba|b\.?com|m\.?com)\b\s*(?:in\s+)?(?:computer\s+science|engineering|information\s+technology|data\s+science|business|finance|science|arts|technology|mathematics|statistics|physics|chemistry|biology|economics|mechanical\s+engineering|electrical\s+engineering|civil\s+engineering|chemical\s+engineering|aerospace\s+engineering|industrial\s+engineering|machine\s+learning|artificial\s+intelligence|deep\s+learning|computer\s+vision|natural\s+language\s+processing)\b',
            # Full degree names with 'in' pattern: "Master's in Data Science", "PhD in Machine Learning"
            r'(?:bachelor(?:\'s)?|master(?:\'s)?|phd|doctorate|diploma|associate)\s+in\s+(?:computer\s+science|engineering|information\s+technology|data\s+science|business|finance|science|arts|technology|machine\s+learning|artificial\s+intelligence|deep\s+learning|computer\s+vision|natural\s+language\s+processing|mechanical\s+engineering|electrical\s+engineering|civil\s+engineering|chemical\s+engineering|aerospace\s+engineering|industrial\s+engineering)',
            # High school / secondary education (no field required)
            r'(?:high\s+school|secondary\s+school|hsc|ssc|h\.?s\.?c\.?|s\.?s\.?c\.?)\s*(?:diploma|certificate|degree)?',
            # Diploma/associate standalone (no field required)
            r'(?:diploma|associate)(?:\s+(?:degree|certificate))?',
            # Abbreviated degrees alone (fallback)
            r'\b(?:b\.?tech|b\.?e|m\.?tech|m\.?e|b\.?sc|m\.?sc|bsc|msc|bca|mca|bba|mba|b\.?com|m\.?com)\b',
            # Common degree abbreviations with field
            r'\b(?:bs|ba|ms|ma|phd|md|jd|mba|msc|bsc)\b\s*(?:in\s+)?(?:computer\s+science|engineering|information\s+technology|data\s+science|business|finance|machine\s+learning|artificial\s+intelligence)\b',
            # University/college names with degree keywords nearby
            r'(?:university|college|institute)\s+(?:of\s+)?[a-z\s]+(?:bachelor|master|phd|b\.tech|m\.tech|b\.e|m\.e|b\.sc|m\.sc|bsc|msc|bca|mca|bba|mba)',
            # Degree keywords followed by university/college
            r'(?:bachelor|master|phd|b\.tech|m\.tech|b\.e|m\.e|b\.sc|m\.sc|bsc|msc|bca|mca|bba|mba)\s+[a-z\s]*(?:university|college|institute)',
        ]

        found = []
        text_lower = text.lower()

        # Check for degree patterns
        for pattern in degree_patterns:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                if match.strip() not in found:
                    found.append(match.strip())

        return found

    def extract_certifications(self, text: str) -> List[str]:
        """
        Extract certifications from resume text.

        Args:
            text: Resume text

        Returns:
            List of certification names
        """
        cert_keywords = [
            'certified', 'certification', 'certificate', 'aws certified',
            'azure certified', 'google certified', 'pmp', 'scrum master',
            'six sigma', 'cisco', 'ccna', 'ccnp', 'mcsa', 'mcse', 'ocp',
            'oracle certified', 'microsoft certified', 'comptia', 'itil'
        ]

        found = []
        text_lower = text.lower()

        for keyword in cert_keywords:
            if keyword in text_lower:
                pattern = rf'.{{0,40}}{re.escape(keyword)}.{{0,60}}'
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    if match.strip() not in found:
                        found.append(match.strip())

        return found

    def save_skill_dictionary(self, filepath: str):
        """Save current skill dictionary to JSON file."""
        data = {
            'skills': self.skills_dict,
            'aliases': self.aliases
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"Skill dictionary saved to {filepath}")

    def load_skill_dictionary(self, filepath: str):
        """Load skill dictionary from JSON file."""
        with open(filepath, 'r') as f:
            data = json.load(f)

        if 'skills' in data:
            self.skills_dict.update(data['skills'])
        if 'aliases' in data:
            self.aliases.update(data['aliases'])

        # Recompile patterns
        self._compile_patterns()
        logger.info(f"Skill dictionary loaded from {filepath}")


def create_skill_extractor(custom_path: Optional[str] = None) -> SkillExtractor:
    """
    Create a skill extractor with optional custom dictionary.

    Args:
        custom_path: Path to custom skill dictionary JSON

    Returns:
        SkillExtractor instance
    """
    extractor = SkillExtractor()

    if custom_path and Path(custom_path).exists():
        extractor.load_skill_dictionary(custom_path)

    return extractor
