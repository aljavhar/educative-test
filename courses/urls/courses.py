from django.urls import path
from courses.views import CourseListCreateView, CourseDetailView

urlpatterns = [
    path('', CourseListCreateView.as_view(), name='course-list-create'),
    path('<int:pk>/', CourseDetailView.as_view(), name='course-detail'),
]
