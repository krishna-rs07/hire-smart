"""
Job Analyzer Module
Analyzes job descriptions to extract requirements, skills, experience, and education needs.
"""

import re
import logging
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

from .skill_extractor import SkillExtractor
from .text_preprocessor import TextPreprocessor

logger = logging.getLogger(__name__)


@dataclass
class JobRequirements:
    """Structured job requirements extracted from job description."""
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    required_experience: int = 0
    preferred_experience: int = 0
    required_education: List[str] = field(default_factory=list)
    preferred_education: List[str] = field(default_factory=list)
    responsibilities: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            'required_skills': self.required_skills,
            'preferred_skills': self.preferred_skills,
            'required_experience': self.required_experience,
            'preferred_experience': self.preferred_experience,
            'required_education': self.required_education,
            'preferred_education': self.preferred_education,
            'responsibilities': self.responsibilities,
            'benefits': self.benefits
        }


class JobAnalyzer:
    """
    Analyzes job descriptions to extract structured requirements.

    Uses pattern matching, keyword extraction, and NLP to identify:
    - Required vs preferred skills
    - Experience requirements
    - Education requirements
    - Responsibilities
    - Benefits
    """

    # Keywords that indicate required vs preferred
    REQUIRED_KEYWORDS = [
        'required', 'must have', 'mandatory', 'essential', 'necessary',
        'must be', 'should have', 'need', 'needs', 'required skills',
        'requirements:', 'qualifications:', 'must possess'
    ]

    PREFERRED_KEYWORDS = [
        'preferred', 'nice to have', 'desirable', 'bonus', 'plus',
        'advantage', 'beneficial', 'good to have', 'ideal', 'asset',
        'preferred skills', 'nice-to-have', 'additional'
    ]

    EXPERIENCE_PATTERNS = [
        r'(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)',
        r'(\d+)\+?\s*yrs?\s*(?:of\s*)?(?:experience|exp)',
        r'experience\s*(?:of\s*)?(\d+)\+?\s*years?',
        r'minimum\s*(\d+)\s*years?',
        r'at\s*least\s*(\d+)\s*years?',
        r'experience(?:\s+required)?\s*[:\-]?\s*(\d+)\+?\s*years?',
        r'(\d+)\+?\s*years\s+(?:of\s+)?(?:experience\s+)?required',
    ]

    EDUCATION_KEYWORDS = {
        'required': [
            'bachelor', 'master', 'phd', 'doctorate', 'degree', 'diploma',
            'b.tech', 'b.e', 'm.tech', 'm.e', 'b.sc', 'm.sc', 'bca', 'mca',
            'bba', 'mba', 'be', 'bt', 'me', 'mt', 'graduate', 'post graduate'
        ],
        'preferred': [
            'advanced degree', 'master\'s', 'phd preferred', 'doctorate preferred',
            'higher education', 'additional certification'
        ]
    }

    RESPONSIBILITY_KEYWORDS = [
        'responsible for', 'responsibilities', 'duties', 'will be responsible',
        'expected to', 'role includes', 'key responsibilities', 'tasks',
        'job responsibilities', 'day to day', 'day-to-day'
    ]

    BENEFITS_KEYWORDS = [
        'benefits', 'perks', 'we offer', 'offered', 'compensation', 'salary',
        'health insurance', 'dental', 'vision', '401k', 'pension', 'stock',
        'equity', 'bonus', 'vacation', 'pto', 'flexible', 'remote', 'hybrid'
    ]

    def __init__(self, skill_extractor: Optional[SkillExtractor] = None,
                 preprocessor: Optional[TextPreprocessor] = None):
        """
        Initialize the job analyzer.

        Args:
            skill_extractor: SkillExtractor instance (creates default if None)
            preprocessor: TextPreprocessor instance (creates default if None)
        """
        self.skill_extractor = skill_extractor or SkillExtractor()
        self.preprocessor = preprocessor or TextPreprocessor()

    def analyze(self, job_description: str) -> JobRequirements:
        """
        Analyze a job description and extract structured requirements.

        Args:
            job_description: Full job description text

        Returns:
            JobRequirements object with extracted information
        """
        if not job_description or not job_description.strip():
            return JobRequirements()

        # Extract skills using marker-based classification with precedence
        # This handles: explicit skill lists, section-based, and prevents cross-contamination
        required_skills, preferred_skills = self._extract_skills_by_markers(job_description)

        # Filter out non-technical skills (business_domain, soft_skills) from requirements
        technical_categories = {
            'programming_languages', 'web_frameworks', 'databases', 'cloud_devops',
            'data_ml', 'tools_technologies', 'methodologies'
        }
        required_skills = self._filter_technical_skills(required_skills, technical_categories)
        preferred_skills = self._filter_technical_skills(preferred_skills, technical_categories)

        # Deduplicate
        required_skills = list(dict.fromkeys(required_skills))
        preferred_skills = list(dict.fromkeys(preferred_skills))

        # Remove overlap (if a skill is both required and preferred, keep as required)
        preferred_skills = [s for s in preferred_skills if s not in required_skills]

        # Extract experience
        required_exp = self._extract_experience(job_description, required=True)
        preferred_exp = self._extract_experience(job_description, required=False)
        if preferred_exp <= required_exp:
            preferred_exp = required_exp

        # Extract education
        required_edu, preferred_edu = self._extract_education(job_description)

        # Extract responsibilities
        responsibilities = self._extract_responsibilities(job_description)

        # Extract benefits
        benefits = self._extract_benefits(job_description)

        return JobRequirements(
            required_skills=required_skills,
            preferred_skills=preferred_skills,
            required_experience=required_exp,
            preferred_experience=preferred_exp,
            required_education=required_edu,
            preferred_education=preferred_edu,
            responsibilities=responsibilities,
            benefits=benefits
        )

    def _split_sections(self, text: str) -> Dict[str, str]:
        """Split job description into logical sections."""
        sections = {}
        text_lower = text.lower()

        # Section markers
        section_patterns = {
            'requirements': [
                'requirements', 'what you need', 'what we\'re looking for',
                'must have', 'required skills', 'technical requirements',
                'required skill', 'minimum qualification'
            ],
            'qualifications': [
                'qualifications', 'qualification'
            ],
            'preferred': [
                'preferred', 'nice to have', 'desirable', 'bonus', 'plus', 'advantage',
                'additional qualifications', 'preferred qualifications',
                'preferred skill', 'nice-to-have', 'ideal candidate'
            ],
            'education': [
                'education', 'degree', 'qualification'
            ],
            'nice_to_have': [
                'nice to have', 'bonus', 'extra', 'additional', 'ideal candidate'
            ],
            'responsibilities': [
                'responsibilities', 'duties', 'what you\'ll do', 'day to day', 'day-to-day',
                'key responsibilities', 'role', 'job description'
            ],
            'benefits': [
                'benefits', 'perks', 'what we offer', 'compensation', 'we provide'
            ],
            'about': [
                'about us', 'about the company', 'company', 'who we are'
            ]
        }

        # Find section boundaries
        lines = text.split('\n')
        current_section = 'general'
        section_content = {k: [] for k in section_patterns.keys()}
        section_content['general'] = []
        section_content['education'] = []

        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            # Check for section header
            matched = None
            for section, patterns in section_patterns.items():
                for pattern in patterns:
                    if re.match(rf'^{re.escape(pattern)}[:]?\s*$', line_lower) or \
                       re.match(rf'^{re.escape(pattern)}[:\s]', line_lower):
                        matched = section
                        break
                if matched:
                    break

            if matched:
                current_section = matched
                # Also capture content after the colon on the same line (e.g., "Education Required: B.Tech Computer Science")
                if ':' in line_stripped:
                    after_colon = line_stripped.split(':', 1)[1].strip()
                    if after_colon:
                        section_content[current_section].append(after_colon)
                continue

            if line_stripped:
                section_content[current_section].append(line)

        # Join content
        for section, content in section_content.items():
            sections[section] = '\n'.join(content).strip()

        return sections

    def _extract_skills_from_sections(self, text: str) -> List[str]:
        """Extract skills from a text section."""
        if not text.strip():
            return []

        result = self.skill_extractor.extract_skills(text, include_categories=False)
        return result.get('skills', [])

    def _extract_skills_by_markers(self, text: str) -> tuple:
        """
        Extract and classify skills based on explicit section markers and skill lists.

        Precedence order (highest to lowest):
        1. Explicit "Required Skills:" and "Preferred Skills:" lines
        2. Requirements/Qualifications section
        3. Preferred/Nice-to-have section
        4. Ambiguous/unmarked mentions → No automatic classification

        This prevents cross-section contamination (e.g., "Experience Required"
        appearing near a Preferred Skills list should not reclassify preferred skills).

        Key rule: If a skill is explicitly listed under "Preferred Skills:",
        it remains PREFERRED unless it's ALSO explicitly listed under "Required Skills:".
        Section-based mentions (like "Django or Flask" in Requirements) do not
        override explicit Preferred Skills classification.
        """
        # Track skills by source for precedence handling
        explicit_required = set()
        explicit_preferred = set()
        section_required = set()
        section_preferred = set()

        # Split into sections first
        sections = self._split_sections(text)

        # === PRIORITY 1: Explicit "Required Skills:" and "Preferred Skills:" lines ===
        explicit_required_list, explicit_preferred_list = self._extract_explicit_skill_lists(text)
        explicit_required = set(explicit_required_list)
        explicit_preferred = set(explicit_preferred_list)

        # === PRIORITY 2: Requirements/Qualifications section ===
        req_sections_text = sections.get('requirements', '') + ' ' + sections.get('qualifications', '')
        if req_sections_text.strip():
            section_required = set(self._extract_skills_from_sections(req_sections_text))

        # === PRIORITY 3: Preferred/Nice-to-have section ===
        pref_sections_text = sections.get('preferred', '') + ' ' + sections.get('nice_to_have', '')
        if pref_sections_text.strip():
            section_preferred = set(self._extract_skills_from_sections(pref_sections_text))

        # Fallback for descriptions with NO explicit requirements/preferred sections:
        # treat skills in the general/description text as required (they describe the role).
        # Only applies when no section-based or explicit classification was found at all,
        # so unambiguous explicit/preferred sections still take precedence.
        if not (explicit_required or explicit_preferred or section_required or section_preferred):
            general_text = sections.get('general', '') + ' ' + sections.get('about', '')
            # Exclude description text that merely names the role
            section_required |= set(self._extract_skills_from_sections(general_text))

        # Build final required skills:
        # - All explicit required skills
        # - Section required skills, EXCEPT those explicitly listed as preferred
        required_skills = explicit_required | (section_required - explicit_preferred)

        # Build final preferred skills:
        # - All explicit preferred skills
        # - Section preferred skills, EXCEPT those explicitly listed as required
        preferred_skills = explicit_preferred | (section_preferred - explicit_required)

        return list(required_skills), list(preferred_skills)

    def _extract_explicit_skill_lists(self, text: str) -> tuple:
        """
        Extract skills from explicit 'Required Skills:' and 'Preferred Skills:' lines.

        Looks for patterns like:
        - Required Skills: Python, Django, SQL
        - Preferred Skills: AWS, Docker
        - Must Have: Python, Django
        - Nice to Have: AWS, Docker

        Returns:
            (required_skills, preferred_skills)
        """
        required_skills = []
        preferred_skills = []

        lines = text.split('\n')
        for line in lines:
            line_stripped = line.strip()
            line_lower = line_stripped.lower()

            # Check for explicit required skills line
            required_patterns = [
                r'^required\s+skills?\s*[:\-]\s*(.+)$',
                r'^must\s+have\s*[:\-]\s*(.+)$',
                r'^essential\s+skills?\s*[:\-]\s*(.+)$',
                r'^mandatory\s+skills?\s*[:\-]\s*(.+)$',
                r'^qualifications?\s*[:\-]\s*(.+)$',
                r'^requirements?\s*[:\-]\s*(.+)$',
            ]

            # Check for explicit preferred skills line
            preferred_patterns = [
                r'^preferred\s+skills?\s*[:\-]\s*(.+)$',
                r'^nice\s+to\s+have\s*[:\-]\s*(.+)$',
                r'^desirable\s+skills?\s*[:\-]\s*(.+)$',
                r'^bonus\s+skills?\s*[:\-]\s*(.+)$',
                r'^additional\s+skills?\s*[:\-]\s*(.+)$',
                r'^ideal\s+skills?\s*[:\-]\s*(.+)$',
            ]

            # Extract from required patterns
            for pattern in required_patterns:
                match = re.search(pattern, line_lower, re.IGNORECASE)
                if match:
                    skills_text = match.group(1).strip()
                    extracted = self._extract_skills_from_sections(skills_text)
                    required_skills.extend(extracted)
                    break  # Only match first pattern per line

            # Extract from preferred patterns
            for pattern in preferred_patterns:
                match = re.search(pattern, line_lower, re.IGNORECASE)
                if match:
                    skills_text = match.group(1).strip()
                    extracted = self._extract_skills_from_sections(skills_text)
                    preferred_skills.extend(extracted)
                    break  # Only match first pattern per line

        # Deduplicate
        required_skills = list(dict.fromkeys(required_skills))
        preferred_skills = list(dict.fromkeys(preferred_skills))

        return required_skills, preferred_skills

    def _filter_technical_skills(self, skills: List[str], technical_categories: set) -> List[str]:
        """Filter skills to only include those from technical categories."""
        # Get all technical skills from the skill extractor
        technical_skills = set()
        for category in technical_categories:
            if category in self.skill_extractor.skills_dict:
                technical_skills.update(s.lower() for s in self.skill_extractor.skills_dict[category])

        return [skill for skill in skills if skill.lower() in technical_skills]

    def _extract_experience(self, text: str, required: bool = True) -> int:
        """Extract years of experience requirement."""
        text_lower = text.lower()

        # Look for experience patterns
        years = []
        for pattern in self.EXPERIENCE_PATTERNS:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                yrs = int(match)
                if 0 < yrs <= 30:
                    years.append(yrs)

        if not years:
            return 0

        # If required, take minimum; if preferred, take maximum
        if required:
            return min(years)
        return max(years)

    def _extract_education(self, text: str) -> tuple:
        """Extract education requirements from the Requirements/Qualifications/Education sections."""
        required = []
        preferred = []

        # Split into sections
        sections = self._split_sections(text)

        # Look at requirements, qualifications, and education sections for required education
        req_text = (sections.get('requirements', '') + ' ' +
                    sections.get('qualifications', '') + ' ' +
                    sections.get('education', '')).lower()
        pref_text = (sections.get('preferred', '') + ' ' + sections.get('nice_to_have', '')).lower()

        # Check required education - use patterns that capture BOTH degree + field
        # Use non-capturing groups (?:...) so findall returns full matches
        education_patterns = [
            # Full degree names with field: "Bachelor of Science in Computer Science", "Master's in Data Science"
            r'(?:bachelor(?:\'s)?|master(?:\'s)?|phd|doctorate|diploma|associate)\s+(?:of\s+|in\s+)?(?:science|arts|engineering|technology|business|computer\s+science|information\s+technology|data\s+science|machine\s+learning|artificial\s+intelligence)',
            # Abbreviated degrees with field: "B.Tech Computer Science", "M.Tech in Data Science"
            # Allow flexible whitespace (including newlines) between degree and field
            r'\b(?:b\.?tech|b\.?e|m\.?tech|m\.?e|b\.?sc|m\.?sc|bsc|msc|bca|mca|bba|mba|b\.?com|m\.?com)\b\s*(?:in\s+)?(?:computer\s+science|engineering|information\s+technology|data\s+science|business|finance|science|arts|technology|machine\s+learning|artificial\s+intelligence)\b',
            # Common degree abbreviations with field
            r'\b(?:bs|ba|ms|ma|phd|md|jd|mba|msc|bsc)\b\s*(?:in\s+)?(?:computer\s+science|engineering|information\s+technology|data\s+science|business|finance|machine\s+learning|artificial\s+intelligence)\b',
            # Full degree names with 'in' pattern: "Master's in Data Science", "Bachelor in Engineering", "PhD in Machine Learning"
            r'(?:bachelor(?:\'s)?|master(?:\'s)?|phd|doctorate|diploma|associate)\s+in\s+(?:computer\s+science|engineering|information\s+technology|data\s+science|business|finance|science|arts|technology|machine\s+learning|artificial\s+intelligence)',
            # Degree abbreviations alone (fallback - loses field info)
            r'\b(?:b\.?tech|b\.?e|m\.?tech|m\.?e|b\.?sc|m\.?sc|bsc|msc|bca|mca|bba|mba|b\.?com|m\.?com)\b',
        ]

        for pattern in education_patterns:
            matches = re.findall(pattern, req_text)
            for match in matches:
                if isinstance(match, tuple):
                    match = ' '.join(match)
                clean = match.strip()
                if clean and clean not in required:
                    required.append(clean)

        # Check preferred education
        for kw in self.EDUCATION_KEYWORDS['preferred']:
            if kw in pref_text:
                pattern = rf'.{{0,30}}{re.escape(kw)}.{{0,30}}'
                matches = re.findall(pattern, pref_text)
                for match in matches:
                    clean = match.strip()
                    if clean not in preferred:
                        preferred.append(clean)

        return required, preferred

    def _extract_responsibilities(self, text: str) -> List[str]:
        """Extract key responsibilities."""
        responsibilities = []
        text_lower = text.lower()

        for kw in self.RESPONSIBILITY_KEYWORDS:
            if kw in text_lower:
                # Find the section following this keyword (use DOTALL to match across newlines)
                pattern = rf'{re.escape(kw)}[:\s]*(.{{0,500}})'
                matches = re.findall(pattern, text_lower, re.DOTALL)
                for match in matches:
                    # Split by bullet points or newlines
                    items = re.split(r'[\n•\-\*]', match)
                    for item in items:
                        item = item.strip()
                        if len(item) > 10 and item not in responsibilities:  # Lower threshold to catch "Write unit tests"
                            responsibilities.append(item)

        # Also check responsibilities section from split_sections
        sections = self._split_sections(text)
        resp_text = sections.get('responsibilities', '')
        if resp_text:
            items = re.split(r'[\n•\-\*]', resp_text)
            for item in items:
                item = item.strip()
                if len(item) > 10 and item not in responsibilities:  # Lower threshold to catch "Write unit tests"
                    responsibilities.append(item)

        return responsibilities[:10]  # Limit to top 10

    def _extract_benefits(self, text: str) -> List[str]:
        """Extract benefits/perks."""
        benefits = []
        text_lower = text.lower()

        for kw in self.BENEFITS_KEYWORDS:
            if kw in text_lower:
                pattern = rf'{re.escape(kw)}[:\s]*(.{{0,300}})'
                matches = re.findall(pattern, text_lower)
                for match in matches:
                    items = re.split(r'[\n•\-\*]', match)
                    for item in items:
                        item = item.strip()
                        if len(item) > 5 and item not in benefits:
                            benefits.append(item)

        return benefits[:10]  # Limit to top 10

    def extract_keywords_for_matching(self, job_description: str, top_n: int = 100) -> List[str]:
        """
        Extract keywords from job description for semantic matching.

        Args:
            job_description: Job description text
            top_n: Number of top keywords to return

        Returns:
            List of important keywords
        """
        # Preprocess for TF-IDF
        processed = self.preprocessor.clean_for_tfidf(job_description)

        # Extract keywords
        keywords = self.preprocessor.extract_keywords(processed, top_n)

        # Add skills (they're important)
        skills_result = self.skill_extractor.extract_skills(job_description)
        skills = skills_result.get('skills', [])

        # Combine and deduplicate
        all_keywords = list(dict.fromkeys(skills + keywords))

        return all_keywords[:top_n]


def analyze_job(job_description: str) -> JobRequirements:
    """
    Convenience function to analyze a job description.

    Args:
        job_description: Job description text

    Returns:
        JobRequirements object
    """
    analyzer = JobAnalyzer()
    return analyzer.analyze(job_description)