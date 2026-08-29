from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy
from django.db.models import Count, Avg, Q

from .models import Job
from screening.models import ScreeningResult


class JobListView(LoginRequiredMixin, ListView):
    """List all jobs for the current recruiter"""
    model = Job
    template_name = 'jobs/job_list.html'
    context_object_name = 'jobs'
    paginate_by = 10

    def get_queryset(self):
        return Job.objects.filter(company=self.request.user).annotate(
            candidate_count=Count('screening_results')
        ).order_by('-created_at')


class JobDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """Job detail view"""
    model = Job
    template_name = 'jobs/job_detail.html'
    context_object_name = 'job'

    def test_func(self):
        return self.get_object().company == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        job = self.get_object()
        screening_results = ScreeningResult.objects.filter(job=job).select_related('candidate')

        if screening_results.exists():
            total = screening_results.count()
            avg_score = screening_results.aggregate(avg=Avg('overall_score'))['avg'] or 0
            highly_recommended = screening_results.filter(recommendation='Highly Recommended').count()
            recommended = screening_results.filter(recommendation='Recommended').count()
            consider = screening_results.filter(recommendation='Consider').count()
            recommended_plus_consider = recommended + consider

            context['screening_stats'] = {
                'total': total,
                'avg_score': round(avg_score, 1),
                'highly_recommended': highly_recommended,
                'recommended': recommended,
                'consider': consider,
                'not_recommended': screening_results.filter(recommendation='Not Recommended').count(),
                'recommended_plus_consider': recommended_plus_consider,
            }
        return context


class JobCreateView(LoginRequiredMixin, CreateView):
    """Create a new job"""
    model = Job
    template_name = 'jobs/job_form.html'
    fields = ['title', 'description', 'required_skills', 'preferred_skills',
              'minimum_experience', 'education_requirement', 'location', 'employment_type', 'status']

    def form_valid(self, form):
        form.instance.company = self.request.user
        messages.success(self.request, 'Job created successfully!')
        return super().form_valid(form)


class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """Update an existing job"""
    model = Job
    template_name = 'jobs/job_form.html'
    fields = ['title', 'description', 'required_skills', 'preferred_skills',
              'minimum_experience', 'education_requirement', 'location', 'employment_type', 'status']

    def test_func(self):
        return self.get_object().company == self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Job updated successfully!')
        return super().form_valid(form)


class JobDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """Delete a job"""
    model = Job
    template_name = 'jobs/job_confirm_delete.html'
    success_url = reverse_lazy('jobs:job_list')

    def test_func(self):
        return self.get_object().company == self.request.user

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Job deleted successfully!')
        return super().delete(request, *args, **kwargs)


@login_required
def job_dashboard(request, pk):
    """Job-specific dashboard with candidate rankings and analytics"""
    job = get_object_or_404(Job, pk=pk, company=request.user)

    screening_results = ScreeningResult.objects.filter(job=job).select_related('candidate').order_by('-overall_score')

    # Summary stats
    total_candidates = screening_results.count()
    avg_score = screening_results.aggregate(avg=Avg('overall_score'))['avg'] or 0

    highly_recommended = screening_results.filter(recommendation='Highly Recommended').count()
    recommended = screening_results.filter(recommendation='Recommended').count()
    consider = screening_results.filter(recommendation='Consider').count()
    not_recommended = screening_results.filter(recommendation='Not Recommended').count()

    recommended_plus_consider = recommended + consider

    # Recommendation distribution for chart
    rec_dist = screening_results.values('recommendation').annotate(count=Count('id'))
    rec_labels = []
    rec_data = []
    for item in rec_dist:
        rec_labels.append(item['recommendation'])
        rec_data.append(item['count'])

    # Score distribution for chart
    score_bins = [0, 50, 65, 80, 90, 101]
    score_labels = ['<50', '50-64', '65-79', '80-89', '90-100']
    score_data = []
    for i in range(len(score_bins) - 1):
        low, high = score_bins[i], score_bins[i + 1]
        if i == len(score_bins) - 2:
            count = screening_results.filter(overall_score__gte=low, overall_score__lte=high).count()
        else:
            count = screening_results.filter(overall_score__gte=low, overall_score__lt=high).count()
        score_data.append(count)

    # Top matched skills across all screenings
    all_matched = []
    for result in screening_results:
        all_matched.extend(result.matched_skills or [])
    from collections import Counter
    matched_counts = Counter(all_matched)
    top_matched_skills = matched_counts.most_common(10)

    # Common missing skills
    all_missing = []
    for result in screening_results:
        all_missing.extend(result.missing_skills or [])
    missing_counts = Counter(all_missing)
    common_missing_skills = missing_counts.most_common(10)

    context = {
        'job': job,
        'screening_results': screening_results,
        'total_candidates': total_candidates,
        'avg_score': round(avg_score, 1),
        'highly_recommended': highly_recommended,
        'recommended': recommended,
        'consider': consider,
        'not_recommended': not_recommended,
        'recommended_plus_consider': recommended_plus_consider,
        'rec_labels': rec_labels,
        'rec_data': rec_data,
        'score_labels': score_labels,
        'score_data': score_data,
        'top_matched_skills': top_matched_skills,
        'common_missing_skills': common_missing_skills,
    }
    return render(request, 'jobs/job_dashboard.html', context)