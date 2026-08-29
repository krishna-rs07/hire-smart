"""Diagnostic for job analyzer section splitting."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from ml.job_analyzer import JobAnalyzer
from ml.skill_extractor import SkillExtractor

ja = JobAnalyzer(skill_extractor=SkillExtractor())

job_desc = """Job Title: Python Developer
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

sections = ja._split_sections(job_desc)
print("=== SECTIONS ===")
for k, v in sections.items():
    if v.strip():
        print(f"[{k}]")
        print(v[:200])
        print()

# Check what's in req_text
req_text = (sections.get('requirements', '') + ' ' +
            sections.get('qualifications', '') + ' ' +
            sections.get('education', '')).lower()
print("=== REQ_TEXT (for education) ===")
print(req_text[:500])
print("...")

# Check if pattern matches
import re
pattern = r'\b(b\.?tech|b\.?e|m\.?tech|m\.?e|b\.?sc|m\.?sc|bsc|msc|bca|mca|bba|mba|b\.?com|m\.?com)\s+(?:in\s+)?(?:computer\s+science|engineering|information\s+technology|data\s+science|business|finance|science|arts|technology)\b'
matches = re.findall(pattern, req_text)
print(f"\nPattern matches: {matches}")

# Full education extraction
required, preferred = ja._extract_education(job_desc)
print(f"\nExtracted required: {required}")
print(f"Extracted preferred: {preferred}")