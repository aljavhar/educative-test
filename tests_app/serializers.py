"""
Serializers for Topics, Questions, and Test Sessions.

IMPORTANT: The student-facing test serializers NEVER include
the correct_answer field — that stays server-side only.
"""

from rest_framework import serializers
from .models import Topic, Question, TestAttempt, AttemptAnswer
import random


class QuestionSerializer(serializers.ModelSerializer):
    """Full question — for teachers (includes correct_answer)."""

    class Meta:
        model = Question
        fields = [
            'id', 'topic', 'question_text',
            'option_a', 'option_b', 'option_c', 'option_d',
            'correct_answer', 'order_index', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CreateQuestionSerializer(serializers.ModelSerializer):
    """Create/update a question (teacher only)."""

    class Meta:
        model = Question
        fields = [
            'question_text', 'option_a', 'option_b',
            'option_c', 'option_d', 'correct_answer',
        ]


class StudentQuestionSerializer(serializers.ModelSerializer):
    """
    Question for students — NO correct_answer field.
    Options are randomized before returning.
    """
    option_a = serializers.SerializerMethodField()
    option_b = serializers.SerializerMethodField()
    option_c = serializers.SerializerMethodField()
    option_d = serializers.SerializerMethodField()
    _randomized_cache = {}

    class Meta:
        model = Question
        fields = ['id', 'question_text', 'option_a', 'option_b', 'option_c', 'option_d']

    def _get_randomized(self, obj):
        """Randomize options once per question instance."""
        if obj.id not in StudentQuestionSerializer._randomized_cache:
            options = [
                obj.option_a, obj.option_b, obj.option_c, obj.option_d
            ]
            random.shuffle(options)
            StudentQuestionSerializer._randomized_cache[obj.id] = options
        return StudentQuestionSerializer._randomized_cache[obj.id]

    def get_option_a(self, obj):
        return self._get_randomized(obj)[0]

    def get_option_b(self, obj):
        return self._get_randomized(obj)[1]

    def get_option_c(self, obj):
        return self._get_randomized(obj)[2]

    def get_option_d(self, obj):
        return self._get_randomized(obj)[3]


class TopicSerializer(serializers.ModelSerializer):
    """Topic detail — for teachers."""

    group_name = serializers.CharField(source='group.name', read_only=True)
    question_count = serializers.SerializerMethodField()
    course_name = serializers.CharField(source='group.course.name', read_only=True)

    class Meta:
        model = Topic
        fields = [
            'id', 'title', 'content', 'date',
            'group', 'group_name', 'course_name',
            'passing_score', 'max_attempts', 'time_limit_minutes',
            'question_count', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def get_question_count(self, obj):
        return obj.questions.count()


class CreateTopicSerializer(serializers.ModelSerializer):
    """Create/update a topic (teacher only)."""

    class Meta:
        model = Topic
        fields = [
            'title', 'content', 'date', 'group',
            'passing_score', 'max_attempts', 'time_limit_minutes',
        ]

    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnswerInputSerializer(serializers.Serializer):
    """One answer from the student during test submission."""
    question_id = serializers.IntegerField()
    selected_option = serializers.ChoiceField(choices=['A', 'B', 'C', 'D'])


class SubmitTestSerializer(serializers.Serializer):
    """Request body when student submits a test."""
    answers = AnswerInputSerializer(many=True)


class AttemptAnswerDetailSerializer(serializers.ModelSerializer):
    """Shows a student what they answered vs. correct answer."""
    question_text = serializers.CharField(source='question.question_text', read_only=True)
    correct_answer = serializers.CharField(source='question.correct_answer', read_only=True)

    class Meta:
        model = AttemptAnswer
        fields = ['question_id', 'question_text', 'selected_option', 'correct_answer', 'is_correct']


class TestAttemptSerializer(serializers.ModelSerializer):
    """Test result shown after submission."""
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    topic_title = serializers.CharField(source='topic.title', read_only=True)
    answers = AttemptAnswerDetailSerializer(many=True, read_only=True)

    class Meta:
        model = TestAttempt
        fields = [
            'id', 'student', 'student_name', 'topic', 'topic_title',
            'attempt_number', 'score', 'total_questions', 'percentage',
            'passed', 'submitted_at', 'answers',
        ]
        read_only_fields = fields
