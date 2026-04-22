"""
Results Views — for viewing test history.

Students: view their own results
Teachers: view all results
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from tests_app.models import TestAttempt
from tests_app.serializers import TestAttemptSerializer
from users.permissions import IsTeacher


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def result_list_view(request):
    """
    GET /api/v1/results/

    Query params:
        ?student_id=5     → filter by student (teacher only)
        ?topic_id=3       → filter by topic
        ?group_id=2       → filter by group (teacher only)

    Students automatically see only their own results.
    """
    user = request.user
    qs = TestAttempt.objects.filter(is_submitted=True).select_related(
        'student', 'topic', 'topic__group'
    ).order_by('-submitted_at')

    if user.is_student:
        qs = qs.filter(student=user)
    else:
        # Teacher can filter
        student_id = request.query_params.get('student_id')
        group_id = request.query_params.get('group_id')
        if student_id:
            qs = qs.filter(student_id=student_id)
        if group_id:
            qs = qs.filter(topic__group_id=group_id)

    topic_id = request.query_params.get('topic_id')
    if topic_id:
        qs = qs.filter(topic_id=topic_id)

    return Response(TestAttemptSerializer(qs, many=True).data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def result_detail_view(request, pk):
    """
    GET /api/v1/results/{id}/

    Returns full result with per-question answer breakdown.
    Students can only view their own results.
    """
    try:
        attempt = TestAttempt.objects.get(pk=pk)
    except TestAttempt.DoesNotExist:
        return Response({'error': 'Result not found.'}, status=status.HTTP_404_NOT_FOUND)

    # Students can only see their own results
    if request.user.is_student and attempt.student != request.user:
        return Response({'error': 'Forbidden.'}, status=status.HTTP_403_FORBIDDEN)

    return Response(TestAttemptSerializer(attempt).data)
