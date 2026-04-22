"""Views for Course and Group management (teacher-only write access)."""

from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Course, Group
from .serializers import (
    CourseSerializer, CreateCourseSerializer,
    GroupSerializer, CreateGroupSerializer,
)
from users.permissions import IsTeacher
from users.models import User
from users.serializers import UserSerializer


# ─── Course Views ───────────────────────────────────────────────────────────────

class CourseListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/courses/  → List all courses (all authenticated users)
    POST /api/v1/courses/  → Create a course (teacher only)
    """
    queryset = Course.objects.all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateCourseSerializer
        return CourseSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = CreateCourseSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        course = serializer.save()
        return Response(CourseSerializer(course).data, status=status.HTTP_201_CREATED)


class CourseDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/courses/{id}/  → Get course details
    PATCH  /api/v1/courses/{id}/  → Update course (teacher only)
    DELETE /api/v1/courses/{id}/  → Delete course (teacher only)
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]


# ─── Group Views ────────────────────────────────────────────────────────────────

class GroupListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/groups/  → List all groups
    POST /api/v1/groups/  → Create a group (teacher only)
    """

    def get_queryset(self):
        user = self.request.user
        # Students only see their own group
        if user.is_student:
            if user.group:
                return Group.objects.filter(id=user.group.id)
            return Group.objects.none()
        # Teachers see all groups
        return Group.objects.select_related('course').all()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateGroupSerializer
        return GroupSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = CreateGroupSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        group = serializer.save()
        return Response(GroupSerializer(group).data, status=status.HTTP_201_CREATED)


class GroupDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/groups/{id}/  → Group details
    PATCH  /api/v1/groups/{id}/  → Update group (teacher only)
    DELETE /api/v1/groups/{id}/  → Delete group (teacher only)
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def group_students_view(request, pk):
    """
    GET /api/v1/groups/{id}/students/
    List all students in a group.
    """
    try:
        group = Group.objects.get(pk=pk)
    except Group.DoesNotExist:
        return Response({'error': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)

    students = User.objects.filter(group=group, role='student', is_active=True)
    return Response(UserSerializer(students, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher])
def add_student_to_group_view(request, pk):
    """
    POST /api/v1/groups/{id}/add-student/
    Body: { "student_id": 5 }
    Assign a student to this group.
    """
    try:
        group = Group.objects.get(pk=pk)
    except Group.DoesNotExist:
        return Response({'error': 'Group not found.'}, status=status.HTTP_404_NOT_FOUND)

    student_id = request.data.get('student_id')
    if not student_id:
        return Response({'error': 'student_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        student = User.objects.get(pk=student_id, role='student')
    except User.DoesNotExist:
        return Response({'error': 'Student not found.'}, status=status.HTTP_404_NOT_FOUND)

    student.group = group
    student.save()
    return Response({'message': f'{student.full_name} added to {group.name}.'})


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher])
def remove_student_from_group_view(request, pk, student_id):
    """
    POST /api/v1/groups/{id}/remove-student/{student_id}/
    Remove a student from this group.
    """
    try:
        student = User.objects.get(pk=student_id, role='student', group_id=pk)
    except User.DoesNotExist:
        return Response({'error': 'Student not found in this group.'}, status=status.HTTP_404_NOT_FOUND)

    student.group = None
    student.save()
    return Response({'message': f'{student.full_name} removed from group.'})
