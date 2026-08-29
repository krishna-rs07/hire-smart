from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Q, Avg, Count
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import ScreeningResult, ScreeningBatch
from .services import get_screening_service
from jobs.models import Job
from resumes.models import Candidate, Resume


class ScreeningListView(LoginRequiredMixin, ListView):
    """List screening results for the current recruiter's jobs"""
    model = ScreeningResult
    template_name = 'screening/screening_list.html'
    context_object_name = 'results'
    paginate_by = 20

    def get_queryset(self):
        # Only show results for jobs owned by this recruiter
        queryset = ScreeningResult.objects.filter(
            job__company=self.request.user
        ).select_related('candidate', 'job')

        # Filters
        job_id = self.request.GET.get('job')
        if job_id:
            queryset = queryset.filter(job_id=job_id)

        recommendation = self.request.GET.get('recommendation')
        if recommendation:
            queryset = queryset.filter(recommendation=recommendation)

        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(candidate__name__icontains=search) |
                Q(candidate__email__icontains=search)
            )

        # Sorting
        sort = self.request.GET.get('sort', '-overall_score')
        valid_sorts = ['overall_score', '-overall_score', 'skill_score', '-skill_score',
                       'candidate__total_experience', '-candidate__total_experience',
                       'screened_at', '-screened_at']
        if sort in valid_sorts:
            queryset = queryset.order_by(sort)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['jobs'] = Job.objects.filter(company=self.request.user)
        context['recommendation_choices'] = ScreeningResult.RECOMMENDATION_CHOICES
        context['status_choices'] = ScreeningResult.STATUS_CHOICES
        context['current_job'] = self.request.GET.get('job', '')
        context['current_recommendation'] = self.request.GET.get('recommendation', '')
        context['current_status'] = self.request.GET.get('status', '')
        context['current_sort'] = self.request.GET.get('sort', '-overall_score')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class ScreeningDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Detailed screening result view with explainable AI"""
    model = ScreeningResult
    template_name = 'screening/screening_detail.html'
    context_object_name = 'result'

    def test_func(self):
        return self.get_object().job.company == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        result = self.object

        # Calculate progress bar widths
        context['skill_width'] = float(result.skill_score)
        context['semantic_width'] = float(result.semantic_score)
        context['experience_width'] = float(result.experience_score)
        context['education_width'] = float(result.education_score)
        context['preferred_width'] = float(result.preferred_skill_score)

        return context


@login_required
def job_candidate_ranking(request, job_id):
    """Candidate ranking page for a specific job"""
    job = get_object_or_404(Job, pk=job_id, company=request.user)

    results = ScreeningResult.objects.filter(job=job).select_related('candidate').order_by('-overall_score')

    # Apply filters
    search = request.GET.get('search')
    if search:
        results = results.filter(
            Q(candidate__name__icontains=search) |
            Q(candidate__email__icontains=search)
        )

    recommendation = request.GET.get('recommendation')
    if recommendation:
        results = results.filter(recommendation=recommendation)

    status = request.GET.get('status')
    if status:
        results = results.filter(status=status)

    # Get counts for summary cards
    all_results = ScreeningResult.objects.filter(job=job)
    highly_recommended_count = all_results.filter(recommendation='Highly Recommended').count()
    recommended_count = all_results.filter(recommendation='Recommended').count()
    not_recommended_count = all_results.filter(recommendation='Not Recommended').count()

    # Pagination
    paginator = Paginator(results, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'job': job,
        'page_obj': page_obj,
        'results': page_obj.object_list,
        'recommendation_choices': ScreeningResult.RECOMMENDATION_CHOICES,
        'status_choices': ScreeningResult.STATUS_CHOICES,
        'current_recommendation': recommendation or '',
        'current_status': status or '',
        'search_query': search or '',
        'highly_recommended_count': highly_recommended_count,
        'recommended_count': recommended_count,
        'not_recommended_count': not_recommended_count,
    }
    return render(request, 'screening/candidate_ranking.html', context)


@login_required
def update_screening_status(request, pk):
    """Update screening result status (shortlist/reject)"""
    result = get_object_or_404(ScreeningResult, pk=pk, job__company=request.user)

    if request.method == 'POST':
        new_status = request.POST.get('status')
        if new_status in dict(ScreeningResult.STATUS_CHOICES):
            result.status = new_status
            result.save()
            messages.success(request, f'Candidate status updated to {result.get_status_display()}.')
        else:
            messages.error(request, 'Invalid status.')

    return redirect('screening:screening_detail', pk=pk)


@login_required
def screen_candidate(request, candidate_id, job_id):
    """Screen a single candidate for a job using AI"""
    from resumes.models import Candidate
    from jobs.models import Job

    candidate = get_object_or_404(Candidate, pk=candidate_id)
    job = get_object_or_404(Job, pk=job_id, company=request.user)

    # Get the screening service
    service = get_screening_service()

    # Run screening
    result = service.screen_candidate_for_job(candidate, job)

    if not result.get('success'):
        messages.error(request, f'Screening failed: {result.get("error", "Unknown error")}')
        return redirect('screening:candidate_ranking', job_id=job_id)

    # Save screening result
    screening_result = service.create_screening_result(candidate, job, result)

    messages.success(request, f'Candidate screened successfully. Overall match: {screening_result.overall_score:.1f}%')
    return redirect('screening:screening_detail', pk=screening_result.pk)


@login_required
def screen_resume(request, resume_id, job_id):
    """Screen a specific resume for a job using AI"""
    resume = get_object_or_404(Resume, pk=resume_id, uploaded_by=request.user)
    job = get_object_or_404(Job, pk=job_id, company=request.user)

    service = get_screening_service()

    result = service.screen_resume_for_job(resume, job)

    if not result.get('success'):
        messages.error(request, f'Screening failed: {result.get("error", "Unknown error")}')
        return redirect('resumes:resume_detail', pk=resume_id)

    screening_result = service.create_screening_result(resume.candidate, job, result)

    messages.success(request, f'Resume screened successfully. Overall match: {screening_result.overall_score:.1f}%')
    return redirect('screening:screening_detail', pk=screening_result.pk)


@login_required
def batch_screen_job(request, job_id):
    """Run batch screening for all candidates on a job"""
    job = get_object_or_404(Job, pk=job_id, company=request.user)

    if request.method == 'POST':
        service = get_screening_service()
        batch = service.batch_screen_job(job, created_by=request.user)

        messages.success(request, f'Batch screening completed. {batch.processed_resumes} candidates screened.')
        return redirect('screening:candidate_ranking', job_id=job_id)

    # GET request - show confirmation page
    from resumes.models import Candidate
    candidate_count = Candidate.objects.filter(resumes__status='completed').distinct().count()

    context = {
        'job': job,
        'candidate_count': candidate_count,
    }
    return render(request, 'screening/batch_screen_confirm.html', context)


@login_required
def auto_screen_on_upload(request, resume_id):
    """Auto-screen a newly uploaded resume against all active jobs"""
    resume = get_object_or_404(Resume, pk=resume_id, uploaded_by=request.user)

    if resume.status != 'completed':
        messages.error(request, 'Resume text not yet extracted. Please wait for processing.')
        return redirect('resumes:resume_detail', pk=resume_id)

    from jobs.models import Job
    active_jobs = Job.objects.filter(company=request.user, status='active')

    if not active_jobs.exists():
        messages.warning(request, 'No active jobs to screen against.')
        return redirect('resumes:resume_detail', pk=resume_id)

    service = get_screening_service()
    screened_count = 0

    for job in active_jobs:
        result = service.screen_resume_for_job(resume, job)
        if result.get('success'):
            service.create_screening_result(resume.candidate, job, result)
            screened_count += 1

    messages.success(request, f'Auto-screened against {screened_count} active job(s).')
    return redirect('resumes:resume_detail', pk=resume_id)


@require_http_methods(["POST"])
@login_required
def extract_resume_text(request, resume_id):
    """Extract text from uploaded resume file"""
    resume = get_object_or_404(Resume, pk=resume_id, uploaded_by=request.user)

    service = get_screening_service()
    success = service.extract_resume_text(resume)

    if success:
        messages.success(request, 'Resume text extracted successfully.')
    else:
        messages.error(request, f'Text extraction failed: {resume.error_message}')

    return redirect('resumes:resume_detail', pk=resume_id)


@login_required
def screening_explanation(request, pk):
    """Detailed explanation view for a screening result (AJAX)"""
    result = get_object_or_404(ScreeningResult, pk=pk, job__company=request.user)

    # Build detailed explanation data
    explanation_data = {
        'overall_score': float(result.overall_score),
        'skill_score': float(result.skill_score),
        'semantic_score': float(result.semantic_score),
        'experience_score': float(result.experience_score),
        'education_score': float(result.education_score),
        'preferred_skill_score': float(result.preferred_skill_score),
        'matched_skills': result.matched_skills,
        'missing_skills': result.missing_skills,
        'missing_preferred_skills': result.missing_preferred_skills,
        'explanation': result.explanation,
        'strengths': result.strengths,
        'weaknesses': result.weaknesses,
        'recommendation': result.recommendation,
        'disclaimer': ("This is an AI-assisted decision support tool. "
                       "Final hiring decisions should be made by qualified human evaluators. "
                       "This system does not consider protected characteristics and is designed "
                       "to reduce bias, but human oversight is essential.")
    }

    return JsonResponse(explanation_data)