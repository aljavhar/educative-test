from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom admin for our User model."""

    list_display = ['username', 'full_name', 'role', 'group', 'is_active', 'created_at']
    list_filter = ['role', 'is_active', 'group']
    search_fields = ['username', 'full_name', 'email']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('EduPlatform', {'fields': ('full_name', 'role', 'group')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('EduPlatform', {'fields': ('full_name', 'role', 'group')}),
    )
