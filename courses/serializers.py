"""Serializers for Courses and Groups."""

from rest_framework import serializers
from .models import Course, Group


class CourseSerializer(serializers.ModelSerializer):
    group_count = serializers.SerializerMethodField()
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'name', 'description', 'group_count', 'created_by_name', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_group_count(self, obj):
        return obj.groups.count()

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by else None


class CreateCourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['name', 'description']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class GroupSerializer(serializers.ModelSerializer):
    course_name = serializers.CharField(source='course.name', read_only=True)
    student_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Group
        fields = ['id', 'name', 'course', 'course_name', 'student_count', 'created_at']
        read_only_fields = ['id', 'created_at']


class CreateGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['name', 'course']

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
