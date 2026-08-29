from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse

from jobs.models import Job
from resumes.models import Candidate


class ScreeningResult(models.Model):
    """AI screening result for a candidate-job pair"""

    RECOMMENDATION_CHOICES = [
        ('Highly Recommended', 'Highly Recommended'),
        ('Recommended', 'Recommended'),
        ('Consider', 'Consider'),
        ('Not Recommended', 'Not Recommended'),
    ]

    STATUS_CHOICES = [
        ('new', 'New'),
        ('screened', 'Screened'),
        ('shortlisted', 'Shortlisted'),
        ('rejected', 'Rejected'),
        ('hired', 'Hired'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='screening_results')
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='screening_results')

    # Overall scores (0-100)
    overall_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    skill_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    semantic_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    experience_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    education_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    preferred_skill_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    # Skill details
    matched_skills = models.JSONField(default=list)
    missing_skills = models.JSONField(default=list)
    missing_preferred_skills = models.JSONField(default=list)

    # Explanation
    explanation = models.TextField(blank=True)
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)

    # Recommendation
    recommendation = models.CharField(max_length=30, choices=RECOMMENDATION_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')

    # Metadata
    screened_at = models.DateTimeField(default=timezone.now)
    screened_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-overall_score', '-screened_at']
        unique_together = ['candidate', 'job']
        verbose_name = 'Screening Result'
        verbose_name_plural = 'Screening Results'
        indexes = [
            models.Index(fields=['job', '-overall_score']),
            models.Index(fields=['candidate', '-screened_at']),
            models.Index(fields=['recommendation']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.candidate.name} - {self.job.title}: {self.overall_score}%"

    def get_absolute_url(self):
        return reverse('screening:screening_detail', kwargs={'pk': self.pk})

    def get_recommendation_badge_class(self):
        """Return CSS class for recommendation badge"""
        mapping = {
            'Highly Recommended': 'recommended',
            'Recommended': 'recommended',
            'Consider': 'consider',
            'Not Recommended': 'rejected',
        }
        return mapping.get(self.recommendation, 'secondary')

    def get_score_color(self):
        """Return color class based on score"""
        score = float(self.overall_score)
        if score >= 90:
            return 'success'
        elif score >= 80:
            return 'info'
        elif score >= 65:
            return 'warning'
        return 'danger'


class ScreeningBatch(models.Model):
    """Batch screening job for multiple resumes"""
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='screening_batches')
    name = models.CharField(max_length=200)
    total_resumes = models.PositiveIntegerField(default=0)
    processed_resumes = models.PositiveIntegerField(default=0)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ], default='pending')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.job.title}"