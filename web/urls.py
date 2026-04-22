"""
Web URL konfiguratsiyasi.
Barcha browser-based sahifalar uchun URL'lar.
"""

from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    # ─── Autentifikatsiya ─────────────────────────────────────────────────────
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.home, name='home'),

    # ─── O'qituvchi sahifalari ────────────────────────────────────────────────
    path('teacher/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/courses/', views.teacher_courses, name='teacher_courses'),
    path('teacher/groups/', views.teacher_groups, name='teacher_groups'),
    path('teacher/topics/', views.teacher_topics, name='teacher_topics'),
    path('teacher/topics/<int:topic_id>/', views.teacher_topic_detail, name='teacher_topic_detail'),
    path('teacher/students/', views.teacher_students, name='teacher_students'),
    path('teacher/analytics/', views.teacher_analytics, name='teacher_analytics'),

    # ─── O'quvchi sahifalari ──────────────────────────────────────────────────
    path('student/', views.student_dashboard, name='student_dashboard'),
    path('student/test/<int:topic_id>/', views.student_test, name='student_test'),
    path('student/submit/<int:attempt_id>/', views.student_submit_test, name='student_submit_test'),
    path('student/results/', views.student_results, name='student_results'),
    path('student/results/<int:attempt_id>/', views.student_result_detail, name='student_result_detail'),
]
