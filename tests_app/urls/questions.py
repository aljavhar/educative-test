from django.urls import path
from tests_app.views import topic_questions_view, question_detail_view

urlpatterns = [
    path('topic/<int:topic_id>/', topic_questions_view, name='topic-questions'),
    path('<int:pk>/', question_detail_view, name='question-detail'),
]
