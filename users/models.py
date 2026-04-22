"""
Users App — Custom User model with Teacher/Student roles.

The User model extends Django's AbstractUser so we keep all
the built-in auth features (password hashing, admin panel, etc.)
and just add our own fields on top.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """
    Custom user model.
    
    Roles:
      - teacher: can create courses, groups, topics, questions, view analytics
      - student: can take tests, view own results
    """

    class Role(models.TextChoices):
        TEACHER = 'teacher', 'Teacher'
        STUDENT = 'student', 'Student'

    # Override email to make it optional (students may not have email)
    email = models.EmailField(blank=True, null=True)

    # Full display name
    full_name = models.CharField(max_length=150)

    # Teacher or student
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.STUDENT,
    )

    # Students belong to one group (class).
    # null=True means teacher accounts don't need a group.
    group = models.ForeignKey(
        'courses.Group',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students',
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.full_name} ({self.role})'

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT
