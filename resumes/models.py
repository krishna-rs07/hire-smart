from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse


class Candidate(models.Model):
    """Candidate profile extracted from resume"""
    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    education = models.TextField(blank=True)
    total_experience = models.PositiveIntegerField(default=0, help_text="Total years of experience")
    skills = models.JSONField(default=list, help_text="List of extracted skills")
    certifications = models.JSONField(default=list, help_text="List of certifications")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Candidate'
        verbose_name_plural = 'Candidates'
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('resumes:candidate_detail', kwargs={'pk': self.pk})


class Resume(models.Model):
    """Uploaded resume file"""
    FILE_TYPES = [
        ('pdf', 'PDF'),
        ('docx', 'DOCX'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    candidate = models.ForeignKey(Candidate, on_delete=models.CASCADE, related_name='resumes')
    file = models.FileField(upload_to='resumes/%Y/%m/%d/')
    file_type = models.CharField(max_length=10, choices=FILE_TYPES)
    extracted_text = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    file_size = models.PositiveIntegerField(default=0)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_resumes')
    uploaded_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'Resume'
        verbose_name_plural = 'Resumes'
        indexes = [
            models.Index(fields=['status', '-uploaded_at']),
            models.Index(fields=['candidate', '-uploaded_at']),
        ]

    def __str__(self):
        return f"{self.candidate.name} - {self.file.name}"

    def get_file_extension(self):
        return self.file.name.split('.')[-1].lower()