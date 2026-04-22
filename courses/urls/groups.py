from django.urls import path
from courses.views import (
    GroupListCreateView, GroupDetailView,
    group_students_view, add_student_to_group_view,
    remove_student_from_group_view,
)

urlpatterns = [
    path('', GroupListCreateView.as_view(), name='group-list-create'),
    path('<int:pk>/', GroupDetailView.as_view(), name='group-detail'),
    path('<int:pk>/students/', group_students_view, name='group-students'),
    path('<int:pk>/add-student/', add_student_to_group_view, name='group-add-student'),
    path('<int:pk>/remove-student/<int:student_id>/', remove_student_from_group_view, name='group-remove-student'),
]
