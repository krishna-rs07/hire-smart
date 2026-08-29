from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class Job(models.Model):
    """Job posting model"""
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('closed', 'Closed'),
        ('filled', 'Filled'),
    ]

    title = models.CharField(max_length=200)
    company = models.ForeignKey(User, on_delete=models.CASCADE, related_name='jobs')
    description = models.TextField()
    required_skills = models.TextField(help_text="Comma-separated required skills")
    preferred_skills = models.TextField(blank=True, help_text="Comma-separated preferred skills")
    minimum_experience = models.PositiveIntegerField(default=0, help_text="Minimum years of experience")
    education_requirement = models.CharField(max_length=200, blank=True, help_text="e.g., B.Tech, M.Tech, PhD")
    location = models.CharField(max_length=200, blank=True)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
        indexes = [
            models.Index(fields=['status', '-created_at']),
            models.Index(fields=['company', '-created_at']),
        ]

    def __str__(self):
        return f"{self.title} at {self.company.username}"

    def get_absolute_url(self):
        return reverse('jobs:job_detail', kwargs={'pk': self.pk})

    def get_required_skills_list(self):
        """Return required skills as a list"""
        return [s.strip() for s in self.required_skills.split(',') if s.strip()]

    def get_preferred_skills_list(self):
        """Return preferred skills as a list"""
        return [s.strip() for s in self.preferred_skills.split(',') if s.strip()]


class JobRequirement(models.Model):
    """Extracted requirements from job description"""
    job = models.OneToOneField(Job, on_delete=models.CASCADE, related_name='extracted_requirements')
    required_skills = models.JSONField(default=list)
    preferred_skills = models.JSONField(default=list)
    education_keywords = models.JSONField(default=list)
    experience_keywords = models.JSONField(default=list)
    technical_keywords = models.JSONField(default=list)
    role_keywords = models.JSONField(default=list)
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Requirements for {self.job.title}"