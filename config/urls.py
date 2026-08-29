"""
URL configuration for Hire Smart project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls', namespace='accounts')),
    path('jobs/', include('jobs.urls', namespace='jobs')),
    path('resumes/', include('resumes.urls', namespace='resumes')),
    path('screening/', include('screening.urls', namespace='screening')),
    path('dashboard/', include('dashboard.urls', namespace='dashboard')),
    path('reports/', include('reports.urls', namespace='reports')),
    path('', views.landing, name='landing'),  # Landing page at root
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)