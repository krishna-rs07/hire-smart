from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
from jobs.models import Job
from screening.models import ScreeningResult


@login_required
def index(request):
    """Reports dashboard - overview of all hiring analytics"""
    user_jobs = Job.objects.filter(company=request.user).prefetch_related('screening_results')

    # Overall stats
    total_jobs = user_jobs.count()
    total_screenings = ScreeningResult.objects.filter(job__company=request.user).count()

    # Per-job summary data
    job_summaries = []
    for job in user_jobs:
        screenings = job.screening_results.all()
        if screenings.exists():
            avg_score = screenings.aggregate(Avg('overall_score'))['overall_score__avg'] or 0
            rec_dist = screenings.values('recommendation').annotate(count=Count('recommendation'))
            rec_counts = {item['recommendation']: item['count'] for item in rec_dist}
            job_summaries.append({
                'job': job,
                'total_screened': screenings.count(),
                'avg_score': round(avg_score, 1),
                'highly_recommended': rec_counts.get('Highly Recommended', 0),
                'recommended': rec_counts.get('Recommended', 0),
                'consider': rec_counts.get('Consider', 0),
                'not_recommended': rec_counts.get('Not Recommended', 0),
            })
        else:
            job_summaries.append({
                'job': job,
                'total_screened': 0,
                'avg_score': 0,
                'highly_recommended': 0,
                'recommended': 0,
                'consider': 0,
                'not_recommended': 0,
            })

    context = {
        'total_jobs': total_jobs,
        'total_screenings': total_screenings,
        'job_summaries': job_summaries,
    }
    return render(request, 'reports/index.html', context)