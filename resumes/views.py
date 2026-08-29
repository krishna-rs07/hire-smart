from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Max
from django.core.paginator import Paginator
from django.http import JsonResponse

from .models import Resume, Candidate
from screening.models import ScreeningResult


class ResumeListView(LoginRequiredMixin, ListView):
    """List all uploaded resumes"""
    model = Resume
    template_name = 'resumes/resume_list.html'
    context_object_name = 'resumes'
    paginate_by = 15

    def get_queryset(self):
        queryset = Resume.objects.select_related('candidate').order_by('-uploaded_at')

        # Filter by status
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)

        # Search
        search = self.request.GET.get('search')
        if search:
            queryset = queryset.filter(
                Q(candidate__name__icontains=search) |
                Q(candidate__email__icontains=search)
            )

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Resume.STATUS_CHOICES
        context['current_status'] = self.request.GET.get('status', '')
        context['search_query'] = self.request.GET.get('search', '')
        return context


class ResumeDetailView(LoginRequiredMixin, DetailView):
    """Resume detail view"""
    model = Resume
    template_name = 'resumes/resume_detail.html'
    context_object_name = 'resume'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Screening results are linked to candidate, not resume directly
        context['screening_results'] = self.object.candidate.screening_results.select_related('job').order_by('-screened_at')
        return context


@login_required
def resume_upload(request):
    """Upload multiple resumes"""
    job_id = request.GET.get('job')
    job = None
    if job_id:
        from jobs.models import Job
        job = get_object_or_404(Job, pk=job_id, company=request.user)

    if request.method == 'POST':
        files = request.FILES.getlist('resumes')
        if not files:
            messages.error(request, 'Please select at least one resume file.')
            return redirect('resumes:resume_upload')

        success_count = 0
        error_count = 0

        for file in files:
            # Validate file
            ext = file.name.split('.')[-1].lower()
            if ext not in ['pdf', 'docx']:
                messages.error(request, f'{file.name}: Unsupported file format. Only PDF and DOCX are allowed.')
                error_count += 1
                continue

            if file.size > 10 * 1024 * 1024:  # 10MB
                messages.error(request, f'{file.name}: File too large. Maximum size is 10MB.')
                error_count += 1
                continue

            # Create candidate with basic info from filename
            candidate_name = file.name.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ').title()
            candidate, created = Candidate.objects.get_or_create(
                name=candidate_name,
                defaults={'email': '', 'phone': ''}
            )

            # Create resume record
            resume = Resume.objects.create(
                candidate=candidate,
                file=file,
                file_type=ext,
                file_size=file.size,
                uploaded_by=request.user,
                status='pending'
            )

            success_count += 1

        if success_count:
            messages.success(request, f'{success_count} resume(s) uploaded successfully. Processing will begin shortly.')
        if error_count:
            messages.warning(request, f'{error_count} file(s) failed validation.')

        if job:
            return redirect('jobs:job_dashboard', pk=job.pk)
        return redirect('resumes:resume_list')

    context = {'job': job}
    return render(request, 'resumes/resume_upload.html', context)


@login_required
def candidate_list(request):
    """List all candidates with search, filtering, and sorting"""
    user = request.user

    # Start with candidates that have resumes uploaded by this user
    candidates = Candidate.objects.filter(resumes__uploaded_by=user).distinct()

    # ---- Search ----
    search = request.GET.get('search')
    if search:
        candidates = candidates.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(skills__icontains=search)
        )

    # ---- Filter by job ----
    job_id = request.GET.get('job')
    selected_job = None
    if job_id:
        from jobs.models import Job
        selected_job = get_object_or_404(Job, pk=job_id, company=user)
        candidates = candidates.filter(screening_results__job=selected_job)

    # ---- Filter by recommendation ----
    recommendation = request.GET.get('recommendation')
    if recommendation:
        candidates = candidates.filter(screening_results__recommendation=recommendation)

    sample_jobs = Job.objects.filter(company=user).order_by('-created_at')
    sample_recommendations = ScreeningResult.RECOMMENDATION_CHOICES

    # ---- Annotate with best screening score for this recruiter's jobs ----
    candidates = candidates.annotate(
        best_score=Max('screening_results__overall_score'),
    )

    # ---- Sorting ----
    sort = request.GET.get('sort')
    if sort == 'score_desc':
        candidates = candidates.order_by('-best_score', 'name')
    elif sort == 'score_asc':
        candidates = candidates.order_by('best_score', 'name')
    elif sort == 'name_asc':
        candidates = candidates.order_by('name')
    elif sort == 'name_desc':
        candidates = candidates.order_by('-name')
    elif sort == 'date_asc':
        candidates = candidates.order_by('created_at')
    else:  # date_desc is default
        candidates = candidates.order_by('-created_at', '-best_score')

    # ---- Pagination ----
    paginator = Paginator(candidates, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'search_query': search or '',
        'selected_job': selected_job,
        'current_job': job_id or '',
        'jobs': sample_jobs,
        'recommendation_choices': sample_recommendations,
        'current_recommendation': recommendation or '',
        'sort': sort or 'date_desc',
    }
    return render(request, 'resumes/candidate_list.html', context)


@login_required
def candidate_detail(request, pk):
    """Candidate detail view"""
    candidate = get_object_or_404(Candidate, pk=pk)
    resumes = candidate.resumes.all().order_by('-uploaded_at')
    screening_results = candidate.screening_results.select_related('job').order_by('-screened_at')

    context = {
        'candidate': candidate,
        'resumes': resumes,
        'screening_results': screening_results,
    }
    return render(request, 'resumes/candidate_detail.html', context)