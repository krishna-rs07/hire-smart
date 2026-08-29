from django.urls import path
from . import views

app_name = 'screening'

urlpatterns = [
    path('', views.ScreeningListView.as_view(), name='screening_list'),
    path('job/<int:job_id>/', views.job_candidate_ranking, name='candidate_ranking'),
    path('result/<int:pk>/', views.ScreeningDetailView.as_view(), name='screening_detail'),
    path('result/<int:pk>/status/', views.update_screening_status, name='update_status'),
    # AI Screening actions
    path('screen/candidate/<int:candidate_id>/job/<int:job_id>/', views.screen_candidate, name='screen_candidate'),
    path('screen/resume/<int:resume_id>/job/<int:job_id>/', views.screen_resume, name='screen_resume'),
    path('batch/job/<int:job_id>/', views.batch_screen_job, name='batch_screen_job'),
    path('auto-screen/resume/<int:resume_id>/', views.auto_screen_on_upload, name='auto_screen_on_upload'),
    path('extract/resume/<int:resume_id>/', views.extract_resume_text, name='extract_resume_text'),
    path('explanation/<int:pk>/', views.screening_explanation, name='screening_explanation'),
]