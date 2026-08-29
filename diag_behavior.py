"""Diagnostic script to understand actual behavior of ML components."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from ml.skill_extractor import SkillExtractor
from ml.job_analyzer import JobAnalyzer
from ml.similarity_engine import SimilarityEngine

# ============ SKILL EXTRACTOR ============
print("=== SKILL EXTRACTOR ===")
se = SkillExtractor()

tests = [
    ("basic", "I have experience with Python, Django, and PostgreSQL."),
    ("aliases", "I know py and js"),
    ("compound", "Experience with machine learning, natural language processing, and REST API development."),
    ("ml_alias", "Experience with ml"),
    ("ai_alias", "Experience with ai"),
    ("cloud", "Experience with aws"),
    ("node", "I know nodejs"),
    ("dotnet", "I know .net"),
    ("react", "Skills: Python, Django, React"),
    ("special", "C++, C#, .NET, Node.js, Vue.js"),
    ("java_vs_js", "I know javascript"),
]

for label, text in tests:
    result = se.extract_skills(text)
    print(f"{label}: {result['skills']}")

print()
print("=== EXPERIENCE EXTRACTION ===")
exp_tests = [
    ("5 years of experience", "5 years of experience in Python development."),
    ("3-5 years", "3-5 years experience with Django."),
    ("from dates", "Senior Developer, TechCorp (2020-2024)\nJunior Developer, StartupInc (2018-2020)"),
    ("none", "I am a student learning Python."),
]
for label, text in exp_tests:
    print(f"{label}: {se.extract_experience_years(text)}")

print()
print("=== EDUCATION EXTRACTION (SkillExtractor) ===")
edu_tests = [
    ("bsc", "Bachelor of Science in Computer Science, University of Tech, 2020"),
    ("mtech", "M.Tech in Computer Science, IIT Delhi, 2022"),
    ("phd", "PhD in Machine Learning, Stanford University, 2023"),
    ("diploma", "Diploma in Mechanical Engineering, Government Polytechnic, 2019"),
    ("multi", "B.Tech Computer Science, 2018\nM.Tech Data Science, 2020"),
]
for label, text in edu_tests:
    print(f"{label}: {se.extract_education(text)}")

# ============ JOB ANALYZER ============
print()
print("=== JOB ANALYZER ===")
ja = JobAnalyzer(skill_extractor=se)

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

req = ja.analyze(job_desc)
print(f"required_skills: {req.required_skills}")
print(f"preferred_skills: {req.preferred_skills}")
print(f"required_experience: {req.required_experience}")
print(f"preferred_experience: {req.preferred_experience}")
print(f"required_education: {req.required_education}")
print(f"preferred_education: {req.preferred_education}")
print(f"responsibilities: {req.responsibilities}")

# ============ SIMILARITY ENGINE ============
print()
print("=== SIMILARITY ENGINE ===")
sim = SimilarityEngine(skill_extractor=se)

pairs = [
    ("identical", "Python developer with Django and PostgreSQL experience",
     "Python developer with Django and PostgreSQL experience"),
    ("very_similar", "Python developer with Django and PostgreSQL experience",
     "Python developer with Django and Postgres experience"),
    ("django_vs_postgres", "Python Django PostgreSQL", "Python Django Postgres"),
    ("different", "Python developer with Django experience",
     "Mechanical engineer with AutoCAD and SolidWorks experience"),
    ("empty", "", "Python developer"),
]

for label, t1, t2 in pairs:
    score = sim.compute_similarity(t1, t2)
    print(f"{label}: {score}")
