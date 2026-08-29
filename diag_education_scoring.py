"""Test education scoring with the fix."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from ml.scoring_engine import ScoringEngine
from ml.job_analyzer import JobAnalyzer
from ml.skill_extractor import SkillExtractor

se = SkillExtractor()
ja = JobAnalyzer(skill_extractor=se)
engine = ScoringEngine()

# Job requires B.Tech Computer Science
job_desc = """Job Title: Python Developer
Company: TechCorp
Requirements:
- B.Tech Computer Science
- Python, Django"""

req = ja.analyze(job_desc)
print(f"Job required education: {req.required_education}")

# Candidate 1: B.Tech Computer Science (exact match)
resume1 = """B.Tech Computer Science, 2020
Python, Django"""
score1 = engine._score_education(resume1, req.required_education, [])
print(f"B.Tech CS candidate: {score1}")

# Candidate 2: Bachelor of Arts in English Literature (different field)
resume2 = """Bachelor of Arts in English Literature, 2023
Python, Django"""
score2 = engine._score_education(resume2, req.required_education, [])
print(f"B.A. English candidate: {score2}")

# Candidate 3: M.Tech Computer Science (higher level, same field)
resume3 = """M.Tech Computer Science, 2022
Python, Django"""
score3 = engine._score_education(resume3, req.required_education, [])
print(f"M.Tech CS candidate: {score3}")

# Candidate 4: B.Tech Mechanical Engineering (same level, different field)
resume4 = """B.Tech Mechanical Engineering, 2020
Python, Django"""
score4 = engine._score_education(resume4, req.required_education, [])
print(f"B.Tech Mechanical candidate: {score4}")

# Candidate 5: No degree
resume5 = """Self-taught
Python, Django"""
score5 = engine._score_education(resume5, req.required_education, [])
print(f"No degree candidate: {score5}")

# Check what _extract_education_fields returns for job
print()
print("Job required fields:", engine._extract_education_fields(req.required_education))
print("Candidate 1 fields:", engine._extract_education_fields(se.extract_education(resume1)))
print("Candidate 2 fields:", engine._extract_education_fields(se.extract_education(resume2)))
print("Candidate 3 fields:", engine._extract_education_fields(se.extract_education(resume3)))
print("Candidate 4 fields:", engine._extract_education_fields(se.extract_education(resume4)))