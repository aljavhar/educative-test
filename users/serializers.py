"""
Serializers for the Users app.
Serializers convert Python objects ↔ JSON.
"""

from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """
    Read-only user representation — safe to return to clients.
    Does NOT include the password.
    """

    group_name = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'full_name', 'email',
            'role', 'group', 'group_name', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_group_name(self, obj):
        """Return the name of the student's group, if they have one."""
        return obj.group.name if obj.group else None


class CreateUserSerializer(serializers.ModelSerializer):
    """
    For creating new users. Accepts and hashes a plain-text password.
    """

    password = serializers.CharField(
        write_only=True,         # Never return password in response
        required=True,
        validators=[validate_password],
    )

    class Meta:
        model = User
        fields = [
            'username', 'password', 'full_name', 'email', 'role', 'group',
        ]

    def create(self, validated_data):
        """Create user and hash the password properly."""
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)   # This hashes the password
        user.save()
        return user


class UpdateUserSerializer(serializers.ModelSerializer):
    """For updating user profile. Password changes use a separate endpoint."""

    class Meta:
        model = User
        fields = ['full_name', 'email', 'group']


class ChangePasswordSerializer(serializers.Serializer):
    """For changing a user's password."""

    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value


class LoginSerializer(serializers.Serializer):
    """For the login endpoint — takes username and password."""
    username = serializers.CharField()
    password = serializers.CharField()
