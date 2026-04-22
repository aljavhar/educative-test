"""
Test-taking views.

Teacher views: manage topics and questions.
Student views: take tests, submit answers, view results.

Key business logic:
  1. Student requests a test → server returns randomized questions (no correct answers)
  2. Student submits answers → server grades server-side
  3. Attempt is saved permanently in DB
  4. If score < passing_score AND attempts_used < max_attempts → student can retry
"""

import random
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Topic, Question, TestAttempt, AttemptAnswer
from .serializers import (
    TopicSerializer, CreateTopicSerializer,
    QuestionSerializer, CreateQuestionSerializer,
    StudentQuestionSerializer, SubmitTestSerializer,
    TestAttemptSerializer,
)
from users.permissions import IsTeacher


# ─── Topic Views ────────────────────────────────────────────────────────────────

class TopicListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/v1/topics/            → List topics
    POST /api/v1/topics/            → Create topic (teacher only)

    Query params:
        ?group_id=1    → filter by group
        ?date=2024-01-15 → filter by date
    """

    def get_queryset(self):
        user = self.request.user
        qs = Topic.objects.select_related('group', 'group__course')

        if user.is_student:
            # Students only see topics for their group
            if user.group:
                qs = qs.filter(group=user.group)
            else:
                return Topic.objects.none()

        # Filter by query params
        group_id = self.request.query_params.get('group_id')
        date = self.request.query_params.get('date')
        if group_id:
            qs = qs.filter(group_id=group_id)
        if date:
            qs = qs.filter(date=date)

        return qs

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateTopicSerializer
        return TopicSerializer

    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]

    def create(self, request, *args, **kwargs):
        serializer = CreateTopicSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        topic = serializer.save()
        return Response(TopicSerializer(topic).data, status=status.HTTP_201_CREATED)


class TopicDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/v1/topics/{id}/  → Topic details
    PATCH  /api/v1/topics/{id}/  → Update topic (teacher only)
    DELETE /api/v1/topics/{id}/  → Delete topic (teacher only)
    """
    queryset = Topic.objects.all()
    serializer_class = TopicSerializer

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            return [IsAuthenticated(), IsTeacher()]
        return [IsAuthenticated()]


# ─── Question Views (Teacher only) ─────────────────────────────────────────────

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def topic_questions_view(request, topic_id):
    """
    GET  /api/v1/questions/topic/{topic_id}/  → List questions (teacher sees correct answers)
    POST /api/v1/questions/topic/{topic_id}/  → Add a question (teacher only)
    """
    try:
        topic = Topic.objects.get(pk=topic_id)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        questions = topic.questions.all()
        # Teachers see correct answers, students don't
        if request.user.is_teacher:
            return Response(QuestionSerializer(questions, many=True).data)
        else:
            return Response({'error': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'POST':
        if not request.user.is_teacher:
            return Response({'error': 'Only teachers can add questions.'}, status=status.HTTP_403_FORBIDDEN)

        serializer = CreateQuestionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Auto-assign order_index
        last_order = topic.questions.count()
        question = serializer.save(topic=topic, order_index=last_order + 1)
        return Response(QuestionSerializer(question).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated, IsTeacher])
def question_detail_view(request, pk):
    """
    PATCH  /api/v1/questions/{id}/  → Update question
    DELETE /api/v1/questions/{id}/  → Delete question
    """
    try:
        question = Question.objects.get(pk=pk)
    except Question.DoesNotExist:
        return Response({'error': 'Question not found.'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'PATCH':
        serializer = CreateQuestionSerializer(question, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(QuestionSerializer(question).data)

    if request.method == 'DELETE':
        question.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


# ─── Test Taking Views (Students) ───────────────────────────────────────────────

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_test_view(request, topic_id):
    """
    GET /api/v1/tests/{topic_id}/start/

    Returns randomized test questions WITHOUT correct answers.
    The student uses this to display the test UI.

    Also checks:
      - Student belongs to this group
      - Today is the right date
      - Student hasn't exceeded max attempts
    """
    try:
        topic = Topic.objects.get(pk=topic_id)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found.'}, status=status.HTTP_404_NOT_FOUND)

    student = request.user

    # Check if student can take the test
    can_attempt, reason = topic.can_student_attempt(student)
    if not can_attempt:
        return Response({'error': reason}, status=status.HTTP_403_FORBIDDEN)

    # Get questions and randomize their order
    questions = list(topic.questions.all())
    random.shuffle(questions)

    if not questions:
        return Response({'error': 'No questions found for this topic.'}, status=status.HTTP_404_NOT_FOUND)

    attempts_used = topic.get_attempt_count(student)

    return Response({
        'topic_id': topic.id,
        'topic_title': topic.title,
        'topic_content': topic.content,
        'date': str(topic.date),
        'time_limit_minutes': topic.time_limit_minutes,
        'passing_score': topic.passing_score,
        'attempts_used': attempts_used,
        'max_attempts': topic.max_attempts,
        'attempts_remaining': topic.max_attempts - attempts_used,
        'questions': StudentQuestionSerializer(questions, many=True).data,
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_test_view(request, topic_id):
    """
    POST /api/v1/tests/{topic_id}/submit/

    Student submits their answers. Server grades immediately.

    Request body:
        {
            "answers": [
                {"question_id": 1, "selected_option": "A"},
                {"question_id": 2, "selected_option": "C"},
                ...
            ]
        }

    Response: Full test result with correct/incorrect per question.

    Anti-cheating:
        - Checks can_student_attempt before allowing submission
        - is_submitted flag prevents re-submission of same attempt
        - All answers are graded server-side
    """
    try:
        topic = Topic.objects.get(pk=topic_id)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found.'}, status=status.HTTP_404_NOT_FOUND)

    student = request.user

    # Validate they can still attempt
    can_attempt, reason = topic.can_student_attempt(student)
    if not can_attempt:
        return Response({'error': reason}, status=status.HTTP_403_FORBIDDEN)

    # Validate request body
    serializer = SubmitTestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    answers_data = serializer.validated_data['answers']
    answer_map = {a['question_id']: a['selected_option'] for a in answers_data}

    # Get actual questions for this topic
    questions = topic.questions.all()
    if not questions:
        return Response({'error': 'No questions in this topic.'}, status=status.HTTP_400_BAD_REQUEST)

    # Create the attempt record
    attempt_number = topic.get_attempt_count(student) + 1
    attempt = TestAttempt.objects.create(
        student=student,
        topic=topic,
        attempt_number=attempt_number,
    )

    # Grade each question
    correct_count = 0
    for question in questions:
        selected = answer_map.get(question.id)

        if selected is None:
            # Student didn't answer this question — mark wrong
            selected = ''

        is_correct = (selected == question.correct_answer)
        if is_correct:
            correct_count += 1

        AttemptAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=selected or 'A',  # default to A if no answer
            is_correct=is_correct,
        )

    # Save final grade
    total = questions.count()
    attempt.score = correct_count
    attempt.total_questions = total
    attempt.percentage = (correct_count / total * 100) if total > 0 else 0
    attempt.passed = attempt.percentage >= topic.passing_score
    attempt.is_submitted = True
    attempt.submitted_at = timezone.now()
    attempt.save()

    return Response(TestAttemptSerializer(attempt).data, status=status.HTTP_200_OK)
