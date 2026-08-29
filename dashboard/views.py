from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from django.db.models import Count, Avg
from django.utils import timezone
from datetime import timedelta

from jobs.models import Job
from resumes.models import Resume, Candidate
from screening.models import ScreeningResult


class LandingView(TemplateView):
    """Landing page view"""
    template_name = 'landing.html'


def landing(request):
    """Landing page - redirects to dashboard if authenticated"""
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    return render(request, 'landing.html')


@login_required
def index(request):
    """Main dashboard view with statistics and charts"""
    user = request.user

    # Date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    # Basic stats
    total_jobs = Job.objects.filter(company=user).count()
    active_jobs = Job.objects.filter(company=user, status='active').count()
    total_resumes = Resume.objects.filter(uploaded_by=user).count()
    total_candidates = Candidate.objects.filter(resumes__uploaded_by=user).distinct().count()

    # Screening stats
    screening_results = ScreeningResult.objects.filter(job__company=user)
    screened_candidates = screening_results.count()

    shortlisted = screening_results.filter(status='shortlisted').count()
    rejected = screening_results.filter(status='rejected').count()
    hired = screening_results.filter(status='hired').count()

    avg_match = screening_results.aggregate(avg=Avg('overall_score'))['avg'] or 0

    # Recommendation distribution counts (for stat cards)
    highly_recommended_count = screening_results.filter(recommendation='Highly Recommended').count()
    recommended_count = screening_results.filter(recommendation='Recommended').count()
    consider_count = screening_results.filter(recommendation='Consider').count()
    not_recommended_count = screening_results.filter(recommendation='Not Recommended').count()

    # Recent activity
    recent_jobs = Job.objects.filter(company=user).order_by('-created_at')[:5]
    recent_resumes = Resume.objects.filter(uploaded_by=user).select_related('candidate').order_by('-uploaded_at')[:5]
    recent_screenings = screening_results.select_related('candidate', 'job').order_by('-screened_at')[:5]

    # Charts data
    # Recommendation distribution
    rec_dist = screening_results.values('recommendation').annotate(count=Count('id'))
    rec_labels = []
    rec_data = []
    for item in rec_dist:
        rec_labels.append(item['recommendation'])
        rec_data.append(item['count'])

    # Status distribution
    status_dist = screening_results.values('status').annotate(count=Count('id'))
    status_labels = []
    status_data = []
    for item in status_dist:
        status_labels.append(item['status'].title())
        status_data.append(item['count'])

    # Weekly screening activity
    weekly_data = []
    weekly_labels = []
    for i in range(6, -1, -1):
        date = today - timedelta(days=i)
        count = screening_results.filter(screened_at__date=date).count()
        weekly_labels.append(date.strftime('%a'))
        weekly_data.append(count)

    # Score distribution (binned)
    score_bins = [0, 50, 65, 80, 90, 101]
    score_labels = ['<50', '50-64', '65-79', '80-89', '90-100']
    score_data = []
    for i in range(len(score_bins) - 1):
        low, high = score_bins[i], score_bins[i + 1]
        if i == len(score_bins) - 2:  # last bin includes 100
            count = screening_results.filter(overall_score__gte=low, overall_score__lte=high).count()
        else:
            count = screening_results.filter(overall_score__gte=low, overall_score__lt=high).count()
        score_data.append(count)

    # Top skills from jobs
    jobs_with_skills = Job.objects.filter(company=user).values_list('required_skills', flat=True)
    skill_counts = {}
    for skills_text in jobs_with_skills:
        for skill in skills_text.split(','):
            skill = skill.strip()
            if skill:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1

    top_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    top_skills_labels = [s[0] for s in top_skills]
    top_skills_data = [s[1] for s in top_skills]

    context = {
        # Stats cards
        'total_jobs': total_jobs,
        'active_jobs': active_jobs,
        'total_resumes': total_resumes,
        'total_candidates': total_candidates,
        'screened_candidates': screened_candidates,
        'shortlisted_candidates': shortlisted,
        'rejected_candidates': rejected,
        'hired_candidates': hired,
        'avg_match_score': round(avg_match, 1),
        'highly_recommended_count': highly_recommended_count,
        'recommended_count': recommended_count,
        'consider_count': consider_count,
        'not_recommended_count': not_recommended_count,

        # Recent items
        'recent_jobs': recent_jobs,
        'recent_resumes': recent_resumes,
        'recent_screenings': recent_screenings,

        # Chart data (JSON for JavaScript)
        'rec_labels': rec_labels,
        'rec_data': rec_data,
        'status_labels': status_labels,
        'status_data': status_data,
        'weekly_labels': weekly_labels,
        'weekly_data': weekly_data,
        'score_labels': score_labels,
        'score_data': score_data,
        'top_skills_labels': top_skills_labels,
        'top_skills_data': top_skills_data,
    }
    return render(request, 'dashboard/index.html', context)