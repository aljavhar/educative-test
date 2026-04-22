"""
User management URLs (teacher-only admin operations).
"""

from django.urls import path
from users.views import UserListCreateView, UserDetailView, change_password_view

urlpatterns = [
    # GET /api/v1/users/               → list all users
    # POST /api/v1/users/              → create new user
    path('', UserListCreateView.as_view(), name='user-list-create'),

    # GET    /api/v1/users/{id}/       → get user
    # PATCH  /api/v1/users/{id}/       → update user
    # DELETE /api/v1/users/{id}/       → delete user
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),

    # POST /api/v1/users/change-password/  → change own password
    path('change-password/', change_password_view, name='change-password'),
]
