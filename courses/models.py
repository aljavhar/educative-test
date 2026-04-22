"""
Courses App — Course and Group (class) models.

A Course is a subject like "Mathematics" or "English".
A Group is a class of students that study one course together.

Relationships:
    Course → has many Groups
    Group  → has many Students (Users)
    Group  → has many Topics (daily lessons)
"""

from django.db import models


class Course(models.Model):
    """
    A subject/discipline, e.g., "Mathematics", "English", "Programming".
    
    Teachers create courses, then create groups for each course.
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    # Track who created the course
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_courses',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'courses'
        ordering = ['name']

    def __str__(self):
        return self.name


class Group(models.Model):
    """
    A class/group of students studying a specific course.
    
    Example: "Math Group A", "English Beginners", "Python Class 1"
    
    Students are assigned to a group via User.group foreign key.
    """

    name = models.CharField(max_length=100)
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='groups',
    )

    # Track who created the group
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_groups',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'groups'
        unique_together = ['name', 'course']  # No duplicate group names per course
        ordering = ['name']

    def __str__(self):
        return f'{self.name} ({self.course.name})'

    @property
    def student_count(self):
        """How many students are in this group."""
        return self.students.filter(is_active=True).count()
