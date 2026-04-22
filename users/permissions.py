"""
Custom DRF permission classes for role-based access control.

Usage in views:
    permission_classes = [IsAuthenticated, IsTeacher]
    permission_classes = [IsAuthenticated, IsStudent]
"""

from rest_framework.permissions import BasePermission


class IsTeacher(BasePermission):
    """Only allow users with the 'teacher' role."""

    message = "Only teachers can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'teacher'
        )


class IsStudent(BasePermission):
    """Only allow users with the 'student' role."""

    message = "Only students can perform this action."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'student'
        )


class IsTeacherOrReadOnly(BasePermission):
    """
    Teachers can read and write.
    Students can only read (GET, HEAD, OPTIONS).
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return True
        return request.user.role == 'teacher'
