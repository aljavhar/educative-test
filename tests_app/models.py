"""
Tests App — Topic, Question, and TestAttempt models.

This is the heart of the platform:
    Topic    → a daily lesson with questions attached
    Question → MCQ (4 options: A, B, C, D)
    TestAttempt → one student's test submission (saved permanently)
    AttemptAnswer → student's answer for each question

Anti-cheating measures built into the model:
    - is_submitted flag prevents re-submission
    - submitted_at timestamp records exact submission time
    - Answers are immutable after submission
    - attempt_number tracks how many tries a student had
"""

from django.db import models
from django.utils import timezone


class Topic(models.Model):
    """
    A daily lesson/topic for a group.
    
    Teacher creates a topic for a group with a specific date.
    Then adds MCQ questions to it.
    Students in that group can take a test on that topic.
    
    Example:
        Title: "Python Functions"
        Date: 2024-01-15
        Group: Python Class 1
        Passing score: 70%
        Max attempts: 2
        Time limit: 30 minutes
    """

    title = models.CharField(max_length=200)
    content = models.TextField(
        blank=True,
        null=True,
        help_text="Topic content/notes. Can also be used for AI question generation.",
    )

    # Which group of students this topic is for
    group = models.ForeignKey(
        'courses.Group',
        on_delete=models.CASCADE,
        related_name='topics',
    )

    # The date students can take the test (access control)
    date = models.DateField(help_text="Date when students can take the test.")

    # Test settings
    passing_score = models.PositiveIntegerField(
        default=70,
        help_text="Minimum percentage to pass (e.g., 70 means 70%).",
    )
    max_attempts = models.PositiveIntegerField(
        default=2,
        help_text="How many times a student can attempt this test.",
    )
    time_limit_minutes = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Time limit in minutes. Null means no limit.",
    )

    # Track who created it
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_topics',
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'topics'
        ordering = ['-date']

    def __str__(self):
        return f'{self.title} — {self.group} ({self.date})'

    def is_available_today(self):
        """Check if today is the correct date for this test."""
        return self.date == timezone.now().date()

    def get_attempt_count(self, student):
        """How many times has this student attempted this test?"""
        return self.attempts.filter(student=student).count()

    def can_student_attempt(self, student):
        """
        Can this student take this test?
        Checks: correct date, under attempt limit, same group.
        """
        if student.group != self.group:
            return False, "You are not in the group for this topic."
        if not self.is_available_today():
            return False, "This test is only available on the scheduled date."
        attempt_count = self.get_attempt_count(student)
        if attempt_count >= self.max_attempts:
            return False, f"You have used all {self.max_attempts} attempt(s)."
        return True, "OK"


class Question(models.Model):
    """
    A single MCQ question for a topic.
    
    Has 4 options (A, B, C, D) and one correct answer.
    When showing a test to a student, options are randomized.
    
    The correct answer is NEVER sent to the frontend — it's
    only used server-side for grading.
    """

    class CorrectAnswer(models.TextChoices):
        A = 'A', 'Option A'
        B = 'B', 'Option B'
        C = 'C', 'Option C'
        D = 'D', 'Option D'

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='questions',
    )

    question_text = models.TextField()
    option_a = models.CharField(max_length=500)
    option_b = models.CharField(max_length=500)
    option_c = models.CharField(max_length=500)
    option_d = models.CharField(max_length=500)

    # The correct answer — NEVER exposed to students via API
    correct_answer = models.CharField(
        max_length=1,
        choices=CorrectAnswer.choices,
    )

    # Order in which this question appears
    order_index = models.PositiveIntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'questions'
        ordering = ['order_index', 'id']

    def __str__(self):
        return f'Q{self.order_index}: {self.question_text[:60]}...'

    def get_options_randomized(self):
        """
        Return options as a dict with randomized positions.
        This means "A" in the database might appear as "B" to the student.
        """
        import random
        options = [
            ('A', self.option_a),
            ('B', self.option_b),
            ('C', self.option_c),
            ('D', self.option_d),
        ]
        random.shuffle(options)
        randomized = {}
        mapping = {}  # maps original letter → new display letter
        for i, (original_key, text) in enumerate(options):
            display_key = ['A', 'B', 'C', 'D'][i]
            randomized[f'option_{display_key.lower()}'] = text
            mapping[original_key] = display_key
        return randomized, mapping


class TestAttempt(models.Model):
    """
    One student's test attempt.
    
    Created when a student starts a test.
    Marked is_submitted=True when they submit.
    After submission, answers cannot be changed (server enforces this).
    
    Every attempt is saved permanently in the database for analytics.
    """

    student = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='attempts',
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='attempts',
    )

    # Which attempt number is this? (1st, 2nd, 3rd...)
    attempt_number = models.PositiveIntegerField(default=1)

    # Grading results (filled in after submission)
    score = models.PositiveIntegerField(
        default=0,
        help_text="Number of correct answers.",
    )
    total_questions = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(
        default=0.0,
        help_text="Score as a percentage (0-100).",
    )
    passed = models.BooleanField(default=False)

    # Anti-cheating: lock submission
    is_submitted = models.BooleanField(
        default=False,
        help_text="Once True, answers cannot be changed.",
    )

    # Timestamps
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)

    # Randomization mapping — stored so we can grade correctly
    # Maps display answer (what student chose) → original DB answer
    answer_mapping = models.JSONField(
        default=dict,
        help_text="Stores question randomization mapping for grading.",
    )

    class Meta:
        db_table = 'test_attempts'
        # One student can have multiple attempts per topic, but each has a unique number
        unique_together = ['student', 'topic', 'attempt_number']
        ordering = ['-started_at']

    def __str__(self):
        status = 'PASSED' if self.passed else 'FAILED'
        return f'{self.student.full_name} — {self.topic.title} (Attempt {self.attempt_number}) [{status}]'

    def grade(self):
        """
        Grade this attempt by comparing student answers to correct answers.
        Called automatically on submission.
        """
        answers = self.answers.select_related('question').all()
        correct_count = 0

        for answer in answers:
            if answer.is_correct:
                correct_count += 1

        total = answers.count()
        self.score = correct_count
        self.total_questions = total
        self.percentage = (correct_count / total * 100) if total > 0 else 0
        self.passed = self.percentage >= self.topic.passing_score
        self.is_submitted = True
        self.submitted_at = timezone.now()
        self.save()

        return self


class AttemptAnswer(models.Model):
    """
    One question's answer within a test attempt.
    
    Created when student submits the test.
    is_correct is calculated server-side from the correct_answer field on Question.
    """

    attempt = models.ForeignKey(
        TestAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attempt_answers',
    )

    # What the student selected (A, B, C, or D — as displayed to them)
    selected_option = models.CharField(max_length=1)

    # Whether it was correct (calculated at submission time)
    is_correct = models.BooleanField(default=False)

    class Meta:
        db_table = 'attempt_answers'
        unique_together = ['attempt', 'question']  # One answer per question per attempt

    def __str__(self):
        return f'Attempt {self.attempt.id} — Q{self.question.id}: {self.selected_option} ({"✓" if self.is_correct else "✗"})'
