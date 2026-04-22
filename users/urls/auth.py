"""
Authentication URLs.
JWT login, refresh token, logout, and current user profile.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from users.views import MeView
from users.auth_views import LoginView, LogoutView

urlpatterns = [
    # POST /api/v1/auth/login/   → get access + refresh JWT tokens
    path('login/', LoginView.as_view(), name='auth-login'),

    # POST /api/v1/auth/refresh/ → get new access token from refresh token
    path('refresh/', TokenRefreshView.as_view(), name='auth-refresh'),

    # POST /api/v1/auth/logout/  → invalidate tokens
    path('logout/', LogoutView.as_view(), name='auth-logout'),

    # GET  /api/v1/auth/me/      → current user profile
    path('me/', MeView.as_view(), name='auth-me'),
]
