from django.db import models


class Report(models.Model):
    """Placeholder model for future report persistence"""
    name = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Report'
        verbose_name_plural = 'Reports'