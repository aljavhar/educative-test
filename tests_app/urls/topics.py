from django.urls import path
from tests_app.views import TopicListCreateView, TopicDetailView

urlpatterns = [
    path('', TopicListCreateView.as_view(), name='topic-list-create'),
    path('<int:pk>/', TopicDetailView.as_view(), name='topic-detail'),
]
