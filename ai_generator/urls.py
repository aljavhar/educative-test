from django.urls import path
from ai_generator.views import generate_questions_view

urlpatterns = [
    # POST /api/v1/ai/generate-questions/
    path('generate-questions/', generate_questions_view, name='ai-generate-questions'),
]
