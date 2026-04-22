from django.contrib import admin
from .models import Topic, Question, TestAttempt, AttemptAnswer


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 0
    fields = ['question_text', 'option_a', 'option_b', 'option_c', 'option_d', 'correct_answer']


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ['title', 'group', 'date', 'passing_score', 'max_attempts', 'created_at']
    list_filter = ['group', 'date']
    search_fields = ['title']
    inlines = [QuestionInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['topic', 'question_text', 'correct_answer', 'order_index']
    list_filter = ['topic']


class AttemptAnswerInline(admin.TabularInline):
    model = AttemptAnswer
    extra = 0
    readonly_fields = ['question', 'selected_option', 'is_correct']


@admin.register(TestAttempt)
class TestAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'topic', 'attempt_number', 'score', 'percentage', 'passed', 'submitted_at']
    list_filter = ['passed', 'topic']
    readonly_fields = ['student', 'topic', 'score', 'percentage', 'passed', 'submitted_at']
    inlines = [AttemptAnswerInline]
