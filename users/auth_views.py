"""
Custom authentication views.
Login returns JWT tokens + user info in one response.
"""

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import UserSerializer


class LoginView(APIView):
    """
    POST /api/v1/auth/login/
    
    Request body:
        { "username": "john", "password": "secret123" }
    
    Response:
        {
            "access": "eyJ...",   ← short-lived access token (60 min)
            "refresh": "eyJ...",  ← long-lived refresh token (7 days)
            "user": { id, username, full_name, role, ... }
        }
    
    Frontend: Store access token, use it in Authorization header.
    Mobile apps: Store refresh token in secure storage.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()

        if not username or not password:
            return Response(
                {'error': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Django's built-in password check
        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        if not user.is_active:
            return Response(
                {'error': 'Account is deactivated. Please contact admin.'},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data,
        })


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/
    
    Blacklists the refresh token so it can't be reused.
    The access token will expire naturally after 60 minutes.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass   # Even if token is already invalid, logout is successful

        return Response({'message': 'Logged out successfully.'})
