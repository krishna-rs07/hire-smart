from django.urls import path
from . import views

app_name = 'resumes'

urlpatterns = [
    path('', views.ResumeListView.as_view(), name='resume_list'),
    path('upload/', views.resume_upload, name='resume_upload'),
    path('candidates/', views.candidate_list, name='candidate_list'),
    path('candidate/<int:pk>/', views.candidate_detail, name='candidate_detail'),
    path('<int:pk>/', views.ResumeDetailView.as_view(), name='resume_detail'),
]