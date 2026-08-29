"""
Pytest configuration and shared fixtures for ML tests.
"""

import pytest
import os
import sys

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Django setup for tests that need it
@pytest.fixture(scope="session", autouse=True)
def django_setup():
    """Set up Django for tests that need database access."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    import django
    django.setup()
    yield


# Shared fixtures
@pytest.fixture
def sample_python_job():
    """Sample Python Developer job description."""
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


@pytest.fixture
def strong_python_resume():
    """Strong Python Developer resume."""
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
def weak_resume():
    """Weak candidate resume (different field)."""
    return """MECHANICAL ENGINEER
Email: mechanical@email.com

SUMMARY
Mechanical Design Engineer with 5 years experience.

EDUCATION
Diploma in Mechanical Engineering, 2019

SKILLS
AutoCAD, Mechanical Design, Quality Control, Manufacturing, SolidWorks

EXPERIENCE
Design Engineer, MechWorks (2019-Present)
- Created 2D drawings with AutoCAD
- Performed quality inspections"""


# Markers for test categorization
def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line("markers", "integration: Integration tests for full pipeline")
    config.addinivalue_line("markers", "edge_case: Edge case and boundary tests")
    config.addinivalue_line("markers", "slow: Slow running tests")