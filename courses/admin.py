from django.contrib import admin
from .models import Course, Group


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_by', 'created_at']
    search_fields = ['name']


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ['name', 'course', 'student_count', 'created_at']
    list_filter = ['course']
    search_fields = ['name']
