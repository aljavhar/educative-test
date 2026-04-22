"""
Analytics Views — statistics and performance tracking.

Endpoints for:
  - Teacher dashboard summary
  - Student progress (over time)
  - Group performance comparison
  - Recent activity feed
"""

from django.db.models import Avg, Count, Q
from django.utils import timezone
from datetime import timedelta

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from tests_app.models import TestAttempt, Topic
from tests_app.serializers import TestAttemptSerializer
from users.models import User
from users.permissions import IsTeacher
from courses.models import Course, Group


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacher])
def dashboard_stats_view(request):
    """
    GET /api/v1/analytics/dashboard/

    Big-picture numbers for the teacher dashboard.
    """
    today = timezone.now().date()

    total_students = User.objects.filter(role='student', is_active=True).count()
    total_courses = Course.objects.count()
    total_groups = Group.objects.count()
    total_topics = Topic.objects.count()

    # All submitted attempts
    all_attempts = TestAttempt.objects.filter(is_submitted=True)
    total_tests_taken = all_attempts.count()

    # Average pass rate (percentage of passed attempts)
    if total_tests_taken > 0:
        passed_count = all_attempts.filter(passed=True).count()
        avg_pass_rate = round((passed_count / total_tests_taken) * 100, 1)
    else:
        avg_pass_rate = 0

    # Today's activity
    tests_today = all_attempts.filter(submitted_at__date=today).count()
    topics_today = Topic.objects.filter(date=today).count()

    return Response({
        'total_students': total_students,
        'total_courses': total_courses,
        'total_groups': total_groups,
        'total_topics': total_topics,
        'total_tests_taken': total_tests_taken,
        'avg_pass_rate': avg_pass_rate,
        'tests_today': tests_today,
        'topics_today': topics_today,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def student_progress_view(request, student_id):
    """
    GET /api/v1/analytics/student/{student_id}/

    Detailed progress for one student.
    Students can view their own progress. Teachers can view anyone's.
    """
    # Permission check
    if request.user.is_student and request.user.id != student_id:
        return Response({'error': 'Forbidden.'}, status=403)

    try:
        student = User.objects.get(pk=student_id, role='student')
    except User.DoesNotExist:
        return Response({'error': 'Student not found.'}, status=404)

    attempts = TestAttempt.objects.filter(
        student=student, is_submitted=True
    ).order_by('-submitted_at')

    total = attempts.count()
    passed = attempts.filter(passed=True).count()
    failed = attempts.filter(passed=False).count()
    avg_score = attempts.aggregate(avg=Avg('percentage'))['avg'] or 0

    # Last 10 results for history chart
    recent = attempts[:10]

    # Weekly breakdown (last 4 weeks)
    weekly = []
    for i in range(4):
        week_start = timezone.now() - timedelta(weeks=i + 1)
        week_end = timezone.now() - timedelta(weeks=i)
        week_attempts = attempts.filter(submitted_at__range=[week_start, week_end])
        week_passed = week_attempts.filter(passed=True).count()
        week_total = week_attempts.count()
        weekly.append({
            'week': i + 1,
            'attempts': week_total,
            'passed': week_passed,
            'pass_rate': round((week_passed / week_total * 100), 1) if week_total else 0,
        })

    return Response({
        'student_id': student.id,
        'student_name': student.full_name,
        'group': student.group.name if student.group else None,
        'total_attempts': total,
        'passed': passed,
        'failed': failed,
        'avg_score': round(avg_score, 1),
        'weekly_breakdown': weekly,
        'recent_results': TestAttemptSerializer(recent, many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsTeacher])
def group_analytics_view(request, group_id):
    """
    GET /api/v1/analytics/group/{group_id}/

    Performance analytics for an entire group.
    """
    try:
        group = Group.objects.get(pk=group_id)
    except Group.DoesNotExist:
        return Response({'error': 'Group not found.'}, status=404)

    students = User.objects.filter(group=group, role='student', is_active=True)
    student_count = students.count()

    attempts = TestAttempt.objects.filter(
        student__in=students, is_submitted=True
    )

    total_attempts = attempts.count()
    avg_score = attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
    passed = attempts.filter(passed=True).count()
    pass_rate = round((passed / total_attempts * 100), 1) if total_attempts else 0

    # Per-topic breakdown
    topics = Topic.objects.filter(group=group).order_by('-date')
    topic_breakdown = []
    for topic in topics[:10]:  # Last 10 topics
        topic_attempts = attempts.filter(topic=topic)
        t_total = topic_attempts.count()
        t_passed = topic_attempts.filter(passed=True).count()
        t_avg = topic_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
        topic_breakdown.append({
            'topic_id': topic.id,
            'topic_title': topic.title,
            'date': str(topic.date),
            'attempts_count': t_total,
            'avg_score': round(t_avg, 1),
            'pass_rate': round((t_passed / t_total * 100), 1) if t_total else 0,
        })

    return Response({
        'group_id': group.id,
        'group_name': group.name,
        'course_name': group.course.name,
        'student_count': student_count,
        'total_attempts': total_attempts,
        'avg_score': round(avg_score, 1),
        'pass_rate': pass_rate,
        'topic_breakdown': topic_breakdown,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def recent_activity_view(request):
    """
    GET /api/v1/analytics/recent-activity/

    Last 20 test submissions — for the teacher dashboard activity feed.
    Students see only their own activity.
    """
    qs = TestAttempt.objects.filter(is_submitted=True).select_related(
        'student', 'topic'
    ).order_by('-submitted_at')

    if request.user.is_student:
        qs = qs.filter(student=request.user)

    recent = qs[:20]

    data = [
        {
            'id': a.id,
            'student_name': a.student.full_name,
            'topic_title': a.topic.title,
            'score': a.score,
            'percentage': a.percentage,
            'passed': a.passed,
            'submitted_at': a.submitted_at,
        }
        for a in recent
    ]
    return Response(data)
