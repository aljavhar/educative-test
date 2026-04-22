from django.urls import path
from tests_app.views import get_test_view, submit_test_view

urlpatterns = [
    # GET  /api/v1/tests/{topic_id}/start/   → get randomized questions
    path('<int:topic_id>/start/', get_test_view, name='test-start'),
    # POST /api/v1/tests/{topic_id}/submit/  → submit answers
    path('<int:topic_id>/submit/', submit_test_view, name='test-submit'),
]
