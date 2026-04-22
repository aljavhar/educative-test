"""
Views for user management.
Teachers can create/update/delete users.
Students can only view their own profile.
"""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import User
from .serializers import (
    UserSerializer,
    CreateUserSerializer,
    UpdateUserSerializer,
    ChangePasswordSerializer,
)
from .permissions import IsTeacher


class MeView(generics.RetrieveAPIView):
    """
    GET /api/v1/auth/me/
    Returns the currently logged-in user's profile.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user


class UserListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/users/  → List all users (teachers only)
    POST /api/v1/users/  → Create new user (teachers only)
    """

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateUserSerializer
        return UserSerializer

    def get_queryset(self):
        user = self.request.user
        if user.is_teacher:
            # Teachers can see everyone
            return User.objects.all().order_by('-created_at')
        # Students can only see themselves (safety fallback)
        return User.objects.filter(id=user.id)

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = CreateUserSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/users/{id}/  → Get user
    PATCH  /api/v1/users/{id}/  → Update user (teacher only)
    DELETE /api/v1/users/{id}/  → Delete user (teacher only)
    """
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return UpdateUserSerializer
        return UserSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password_view(request):
    """
    POST /api/v1/users/change-password/
    Allows any logged-in user to change their own password.
    """
    serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
    serializer.is_valid(raise_exception=True)

    request.user.set_password(serializer.validated_data['new_password'])
    request.user.save()

    return Response({'message': 'Password changed successfully.'})
