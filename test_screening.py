import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

from ml.pipeline import quick_screen
from screening.models import Candidate, Job, ScreeningResult

# Get the Python Developer job
job = Job.objects.get(title='Python Developer')
job_desc = job.description

# Test all candidates for Python Developer
candidates = Candidate.objects.filter(screening_results__job=job).distinct()

for candidate in candidates:
    resume = candidate.resumes.first()
    if resume:
        result = quick_screen(resume.extracted_text, job_desc)
        print(f'{candidate.name}: {result["overall_score"]:.1f}% - {result["recommendation"]}')
        print(f'  Skill: {result["skill_score"]:.1f}% | Semantic: {result["semantic_score"]:.1f}% | Exp: {result["experience_score"]:.1f}% | Edu: {result["education_score"]:.1f}% | Pref: {result["preferred_skill_score"]:.1f}%')
        print(f'  Job Title: {result.get("job_title_score", "N/A")}%')
        print(f'  Matched: {result["matched_skills"]}')
        print(f'  Missing: {result["missing_skills"]}')
        print()