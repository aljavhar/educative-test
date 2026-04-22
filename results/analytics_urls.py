from django.urls import path
from results.analytics_views import (
    dashboard_stats_view,
    student_progress_view,
    group_analytics_view,
    recent_activity_view,
)

urlpatterns = [
    path('dashboard/', dashboard_stats_view, name='analytics-dashboard'),
    path('student/<int:student_id>/', student_progress_view, name='analytics-student'),
    path('group/<int:group_id>/', group_analytics_view, name='analytics-group'),
    path('recent-activity/', recent_activity_view, name='analytics-recent'),
]
