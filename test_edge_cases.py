import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from ml.pipeline import quick_screen

job_desc = '''Job Title: Python Developer
Company: demo_recruiter
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
Employment Type: Full Time'''

def print_result(label, result):
    print(f'=== {label} ===')
    print(f'Overall Score: {result["overall_score"]:.1f}%')
    print(f'Recommendation: {result["recommendation"]}')
    print(f'Skill: {result["skill_score"]:.1f}%')
    print(f'Semantic: {result["semantic_score"]:.1f}%')
    print(f'Experience: {result["experience_score"]:.1f}%')
    print(f'Education: {result["education_score"]:.1f}%')
    print(f'Preferred: {result["preferred_skill_score"]:.1f}%')
    print(f'Job Title: {result.get("job_title_score", "N/A")}%')
    print(f'Matched: {result["matched_skills"]}')
    print(f'Missing: {result["missing_skills"]}')
    print()

# Test 1: Completely unrelated resume (Mechanical Engineer)
unrelated_resume = '''RAVI CHANDRA
Email: ravi.chandra@email.com | Phone: +91-9949012346 | Vijayawada, Andhra Pradesh

PROFILE
Mechanical Design Engineer.

EDUCATION
Diploma in Mechanical Engineering, Government Polytechnic, 2019

SKILLS
AutoCAD, Mechanical Design, Quality Control, Manufacturing, SolidWorks

EXPERIENCE
Design Engineer, MechWorks (2019-Present)
- Created 2D drawings with AutoCAD
- Performed quality inspections
- Supported production line

Trainee, FactoryTech (2018-2019)
- Learned CAD basics

ACHIEVEMENTS
- Reduced design errors by 25%'''

result = quick_screen(unrelated_resume, job_desc)
print_result("Test 1: Unrelated Resume (Mechanical Engineer)", result)

# Test 2: Resume with no skills
no_skills_resume = '''JOHN DOE
Email: john.doe@email.com

SUMMARY
Recent graduate looking for opportunities.

EDUCATION
Bachelor of Arts in English Literature, University of Arts, 2023

EXPERIENCE
Intern, Marketing Agency (2022-2023)
- Wrote blog posts
- Managed social media

SKILLS
Communication, Writing, Microsoft Office'''

result = quick_screen(no_skills_resume, job_desc)
print_result("Test 2: Resume with No Technical Skills", result)

# Test 3: Empty resume
empty_resume = ''' '''

result = quick_screen(empty_resume, job_desc)
print_result("Test 3: Empty Resume", result)

# Test 4: Resume with only preferred skills
only_preferred = '''JANE SMITH
Email: jane.smith@email.com

SUMMARY
DevOps engineer with cloud experience.

EDUCATION
B.Tech Computer Science, 2020

SKILLS
Docker, AWS, Kubernetes, FastAPI, Celery

EXPERIENCE
DevOps Engineer, CloudCo (2020-Present)
- Managed AWS infrastructure
- Built CI/CD pipelines with Docker
- Used FastAPI for internal tools'''

result = quick_screen(only_preferred, job_desc)
print_result("Test 4: Only Preferred Skills", result)

# Test 5: Resume with wrong experience level
junior_resume = '''JUNIOR DEV
Email: junior@email.com

SUMMARY
Entry-level Python developer.

EDUCATION
B.Tech Computer Science, 2024

SKILLS
Python, Django, Git

EXPERIENCE
Intern, TechStart (2023-2024)
- Learned Python and Django basics'''

result = quick_screen(junior_resume, job_desc)
print_result("Test 5: Junior Developer (0 years exp)", result)

# Test 6: Very short resume
short_resume = '''I know Python and Django.'''

result = quick_screen(short_resume, job_desc)
print_result("Test 6: Very Short Resume", result)

# Test 7: Resume with keyword stuffing
keyword_stuff = '''EXPERT PYTHON DJANGO FLASK REST API POSTGRESQL GIT DEVELOPER
PYTHON DJANGO FLASK REST API POSTGRESQL GIT PYTHON DJANGO FLASK REST API POSTGRESQL GIT
PYTHON DJANGO FLASK REST API POSTGRESQL GIT PYTHON DJANGO FLASK REST API POSTGRESQL GIT

EDUCATION
B.Tech Computer Science, 2018

SKILLS
Python, Django, Flask, REST API, PostgreSQL, Git, Python, Django, Flask, REST API, PostgreSQL, Git

EXPERIENCE
Senior Python Developer, TechCo (2018-Present)
Python Django Flask REST API PostgreSQL Git Python Django Flask REST API PostgreSQL Git'''

result = quick_screen(keyword_stuff, job_desc)
print_result("Test 7: Keyword Stuffing", result)

# Test 8: Resume with matching job title
title_match = '''SENIOR PYTHON DEVELOPER
Email: senior@email.com

SUMMARY
Senior Python Developer with 6 years experience.

EDUCATION
B.Tech Computer Science, 2017

SKILLS
Python, Django, REST API, PostgreSQL, Git

EXPERIENCE
Senior Python Developer, BigTech (2017-Present)
- Built Python Django applications'''

result = quick_screen(title_match, job_desc)
print_result("Test 8: Matching Job Title (Senior Python Developer)", result)

# Test 9: Data Analyst applying for Python Developer
data_analyst = '''DATA ANALYST
Email: analyst@email.com

SUMMARY
Data Analyst with 3 years experience.

EDUCATION
B.Tech Computer Science, 2020

SKILLS
SQL, Python, pandas, Excel, Tableau, Statistics

EXPERIENCE
Data Analyst, DataCorp (2020-Present)
- Analyzed data with Python and SQL
- Built Tableau dashboards'''

result = quick_screen(data_analyst, job_desc)
print_result("Test 9: Data Analyst Applying for Python Dev", result)

# Test 10: Resume with different job title
frontend_resume = '''FRONTEND DEVELOPER
Email: frontend@email.com

SUMMARY
Frontend Developer with React experience.

EDUCATION
B.Tech Computer Science, 2019

SKILLS
JavaScript, React, HTML, CSS, TypeScript

EXPERIENCE
Frontend Developer, WebCo (2019-Present)
- Built React applications
- Used TypeScript and CSS'''

result = quick_screen(frontend_resume, job_desc)
print_result("Test 10: Frontend Developer Applying for Python Dev", result)