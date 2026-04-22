"""
Web Views — Browser orqali ishlaydigan sahifalar uchun views.

Bu views Django session authentication ishlatadi (JWT emas),
chunki HTML template'lar session-based auth bilan ishlaydi.

Teacher sahifalari: /web/teacher/...
Student sahifalari: /web/student/...
"""

import random
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from courses.models import Course, Group
from tests_app.models import AttemptAnswer, Question, TestAttempt, Topic
from users.models import User


# ─── Yordamchi decoratorlar ──────────────────────────────────────────────────

def teacher_required(view_func):
    """Faqat o'qituvchilarga ruxsat beradi."""
    @wraps(view_func)
    @login_required(login_url='web:login')
    def wrapper(request, *args, **kwargs):
        if not request.user.is_teacher:
            messages.error(request, "Bu sahifaga faqat o'qituvchilar kira oladi.")
            return redirect('web:student_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """Faqat o'quvchilarga ruxsat beradi."""
    @wraps(view_func)
    @login_required(login_url='web:login')
    def wrapper(request, *args, **kwargs):
        if not request.user.is_student:
            messages.error(request, "Bu sahifaga faqat o'quvchilar kira oladi.")
            return redirect('web:teacher_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


# ─── Autentifikatsiya ────────────────────────────────────────────────────────

def login_view(request):
    """Login sahifasi."""
    if request.user.is_authenticated:
        return redirect('web:home')

    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('web:home')
        else:
            messages.error(request, "Username yoki parol noto'g'ri. Qaytadan urinib ko'ring.")

    return render(request, 'auth/login.html')


def logout_view(request):
    """Logout qilish."""
    logout(request)
    messages.success(request, "Tizimdan chiqildi.")
    return redirect('web:login')


@login_required(login_url='web:login')
def home(request):
    """Rolga qarab tegishli dashboardga yo'naltiradi."""
    if request.user.is_teacher:
        return redirect('web:teacher_dashboard')
    return redirect('web:student_dashboard')


# ─── O'qituvchi sahifalari ───────────────────────────────────────────────────

@teacher_required
def teacher_dashboard(request):
    """O'qituvchi bosh sahifasi — umumiy statistika."""
    teacher = request.user
    courses = Course.objects.filter(created_by=teacher)
    groups = Group.objects.filter(created_by=teacher)
    topics = Topic.objects.filter(created_by=teacher)
    students = User.objects.filter(role='student', group__in=groups)

    today = timezone.now().date()
    todays_topics = topics.filter(date=today).annotate(
        question_count=Count('questions'),
        attempt_count=Count('attempts'),
    )

    recent_attempts = TestAttempt.objects.filter(
        topic__created_by=teacher,
        is_submitted=True,
    ).select_related('student', 'topic').order_by('-submitted_at')[:8]

    context = {
        'courses_count': courses.count(),
        'groups_count': groups.count(),
        'topics_count': topics.count(),
        'students_count': students.count(),
        'todays_topics': todays_topics,
        'recent_attempts': recent_attempts,
        'today': today,
    }
    return render(request, 'teacher/dashboard.html', context)


@teacher_required
def teacher_courses(request):
    """Kurslarni boshqarish sahifasi."""
    teacher = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            name = request.POST.get('name', '').strip()
            description = request.POST.get('description', '').strip()
            if name:
                Course.objects.create(
                    name=name,
                    description=description,
                    created_by=teacher,
                )
                messages.success(request, f"✓ '{name}' kursi muvaffaqiyatli yaratildi.")
            else:
                messages.error(request, "Kurs nomi kiritilishi shart.")

        elif action == 'delete':
            course_id = request.POST.get('course_id')
            deleted, _ = Course.objects.filter(id=course_id, created_by=teacher).delete()
            if deleted:
                messages.success(request, "Kurs o'chirildi.")

        return redirect('web:teacher_courses')

    courses = Course.objects.filter(created_by=teacher).annotate(
        group_count=Count('groups')
    ).order_by('-created_at')
    return render(request, 'teacher/courses.html', {'courses': courses})


@teacher_required
def teacher_groups(request):
    """Guruhlarni boshqarish sahifasi."""
    teacher = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            name = request.POST.get('name', '').strip()
            course_id = request.POST.get('course_id')
            if name and course_id:
                course = get_object_or_404(Course, id=course_id, created_by=teacher)
                Group.objects.create(name=name, course=course, created_by=teacher)
                messages.success(request, f"✓ '{name}' guruhi muvaffaqiyatli yaratildi.")
            else:
                messages.error(request, "Guruh nomi va kurs tanlanishi shart.")

        elif action == 'delete':
            group_id = request.POST.get('group_id')
            deleted, _ = Group.objects.filter(id=group_id, created_by=teacher).delete()
            if deleted:
                messages.success(request, "Guruh o'chirildi.")

        return redirect('web:teacher_groups')

    groups = Group.objects.filter(created_by=teacher).select_related('course').annotate(
        student_count=Count('students')
    ).order_by('-created_at')
    courses = Course.objects.filter(created_by=teacher)
    return render(request, 'teacher/groups.html', {'groups': groups, 'courses': courses})


@teacher_required
def teacher_topics(request):
    """Mavzularni boshqarish sahifasi."""
    teacher = request.user

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'create':
            title = request.POST.get('title', '').strip()
            group_id = request.POST.get('group_id')
            date = request.POST.get('date')
            passing_score = request.POST.get('passing_score', 70)
            max_attempts = request.POST.get('max_attempts', 2)
            time_limit = request.POST.get('time_limit_minutes') or None
            content = request.POST.get('content', '').strip()

            if title and group_id and date:
                group = get_object_or_404(Group, id=group_id, created_by=teacher)
                Topic.objects.create(
                    title=title,
                    group=group,
                    date=date,
                    passing_score=int(passing_score),
                    max_attempts=int(max_attempts),
                    time_limit_minutes=int(time_limit) if time_limit else None,
                    content=content,
                    created_by=teacher,
                )
                messages.success(request, f"✓ '{title}' mavzusi muvaffaqiyatli yaratildi.")
            else:
                messages.error(request, "Mavzu nomi, guruh va sana majburiy.")

        elif action == 'delete':
            topic_id = request.POST.get('topic_id')
            deleted, _ = Topic.objects.filter(id=topic_id, created_by=teacher).delete()
            if deleted:
                messages.success(request, "Mavzu o'chirildi.")

        return redirect('web:teacher_topics')

    topics = Topic.objects.filter(created_by=teacher).select_related(
        'group__course'
    ).annotate(
        question_count=Count('questions'),
        attempt_count=Count('attempts'),
    ).order_by('-date')
    groups = Group.objects.filter(created_by=teacher).select_related('course')
    today = timezone.now().date()

    return render(request, 'teacher/topics.html', {
        'topics': topics,
        'groups': groups,
        'today': today,
    })


@teacher_required
def teacher_topic_detail(request, topic_id):
    """Mavzu uchun savollarni boshqarish."""
    teacher = request.user
    topic = get_object_or_404(Topic, id=topic_id, created_by=teacher)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'add_question':
            question_text = request.POST.get('question_text', '').strip()
            option_a = request.POST.get('option_a', '').strip()
            option_b = request.POST.get('option_b', '').strip()
            option_c = request.POST.get('option_c', '').strip()
            option_d = request.POST.get('option_d', '').strip()
            correct_answer = request.POST.get('correct_answer', '').strip()

            if all([question_text, option_a, option_b, option_c, option_d, correct_answer]):
                order_index = topic.questions.count() + 1
                Question.objects.create(
                    topic=topic,
                    question_text=question_text,
                    option_a=option_a,
                    option_b=option_b,
                    option_c=option_c,
                    option_d=option_d,
                    correct_answer=correct_answer,
                    order_index=order_index,
                )
                messages.success(request, "✓ Savol muvaffaqiyatli qo'shildi.")
            else:
                messages.error(request, "Barcha maydonlarni to'ldirib, to'g'ri javobni tanlang.")

        elif action == 'delete_question':
            question_id = request.POST.get('question_id')
            Question.objects.filter(id=question_id, topic=topic).delete()
            messages.success(request, "Savol o'chirildi.")

        return redirect('web:teacher_topic_detail', topic_id=topic_id)

    questions = topic.questions.all().order_by('order_index')
    attempts = topic.attempts.filter(is_submitted=True).select_related(
        'student'
    ).order_by('-submitted_at')[:20]

    return render(request, 'teacher/topic_detail.html', {
        'topic': topic,
        'questions': questions,
        'attempts': attempts,
    })


@teacher_required
def teacher_students(request):
    """O'quvchilar ro'yxati."""
    teacher = request.user
    groups = Group.objects.filter(created_by=teacher)
    students = User.objects.filter(
        role='student',
        group__in=groups,
    ).select_related('group', 'group__course').order_by('group', 'full_name')

    # Filter by group
    selected_group_id = request.GET.get('group_id')
    if selected_group_id:
        students = students.filter(group_id=selected_group_id)

    # Add stats for each student
    students_data = []
    for student in students:
        total = TestAttempt.objects.filter(student=student, is_submitted=True).count()
        passed = TestAttempt.objects.filter(student=student, is_submitted=True, passed=True).count()
        avg = TestAttempt.objects.filter(
            student=student, is_submitted=True
        ).aggregate(avg=Avg('percentage'))['avg'] or 0
        students_data.append({
            'student': student,
            'total_attempts': total,
            'passed': passed,
            'avg_percentage': round(avg, 1),
        })

    return render(request, 'teacher/students.html', {
        'students_data': students_data,
        'groups': groups,
        'selected_group_id': selected_group_id,
    })


@teacher_required
def teacher_analytics(request):
    """Analitika va natijalar sahifasi."""
    teacher = request.user
    groups = Group.objects.filter(created_by=teacher).select_related('course')

    selected_group_id = request.GET.get('group_id')
    selected_group = None

    attempts_qs = TestAttempt.objects.filter(
        topic__created_by=teacher,
        is_submitted=True,
    ).select_related('student', 'topic', 'topic__group')

    if selected_group_id:
        selected_group = get_object_or_404(Group, id=selected_group_id, created_by=teacher)
        attempts_qs = attempts_qs.filter(topic__group=selected_group)

    attempts = attempts_qs.order_by('-submitted_at')[:50]

    group_stats = []
    for group in groups:
        group_attempts = TestAttempt.objects.filter(
            topic__group=group,
            topic__created_by=teacher,
            is_submitted=True,
        )
        total = group_attempts.count()
        passed = group_attempts.filter(passed=True).count()
        avg_pct = group_attempts.aggregate(avg=Avg('percentage'))['avg'] or 0
        group_stats.append({
            'group': group,
            'total_attempts': total,
            'passed': passed,
            'failed': total - passed,
            'avg_percentage': round(avg_pct, 1),
        })

    return render(request, 'teacher/analytics.html', {
        'groups': groups,
        'selected_group': selected_group,
        'selected_group_id': selected_group_id,
        'attempts': attempts,
        'group_stats': group_stats,
    })


# ─── O'quvchi sahifalari ─────────────────────────────────────────────────────

@student_required
def student_dashboard(request):
    """O'quvchi bosh sahifasi — bugungi testlar."""
    student = request.user
    today = timezone.now().date()
    topics_info = []

    if student.group:
        todays_topics = Topic.objects.filter(
            group=student.group,
            date=today,
        ).annotate(question_count=Count('questions'))

        for topic in todays_topics:
            attempt_count = topic.get_attempt_count(student)
            best_attempt = TestAttempt.objects.filter(
                student=student,
                topic=topic,
                is_submitted=True,
            ).order_by('-percentage').first()
            can_attempt, reason = topic.can_student_attempt(student)
            topics_info.append({
                'topic': topic,
                'attempt_count': attempt_count,
                'best_attempt': best_attempt,
                'can_attempt': can_attempt,
                'reason': reason if not can_attempt else '',
            })

    recent_results = TestAttempt.objects.filter(
        student=student,
        is_submitted=True,
    ).select_related('topic').order_by('-submitted_at')[:5]

    return render(request, 'student/dashboard.html', {
        'topics_info': topics_info,
        'recent_results': recent_results,
        'today': today,
        'group': student.group,
    })


@student_required
def student_test(request, topic_id):
    """Testni boshlash va savollarni ko'rsatish."""
    student = request.user
    topic = get_object_or_404(Topic, id=topic_id)

    can_attempt, reason = topic.can_student_attempt(student)
    if not can_attempt:
        messages.error(request, reason)
        return redirect('web:student_dashboard')

    questions = list(topic.questions.all().order_by('order_index'))
    if not questions:
        messages.error(request, "Bu mavzuda hali savollar qo'shilmagan.")
        return redirect('web:student_dashboard')

    attempt_number = topic.get_attempt_count(student) + 1
    attempt = TestAttempt.objects.create(
        student=student,
        topic=topic,
        attempt_number=attempt_number,
        total_questions=len(questions),
    )

    questions_data = []
    all_mappings = {}

    for q in questions:
        options = [('A', q.option_a), ('B', q.option_b), ('C', q.option_c), ('D', q.option_d)]
        random.shuffle(options)
        displayed = {}
        mapping = {}
        for i, (orig_key, text) in enumerate(options):
            disp_key = ['A', 'B', 'C', 'D'][i]
            displayed[disp_key] = text
            mapping[disp_key] = orig_key
        questions_data.append({
            'id': q.id,
            'question_text': q.question_text,
            'options': displayed,
            'order_index': q.order_index,
        })
        all_mappings[str(q.id)] = mapping

    attempt.answer_mapping = all_mappings
    attempt.save()

    return render(request, 'student/test.html', {
        'topic': topic,
        'questions': questions_data,
        'attempt': attempt,
        'time_limit': topic.time_limit_minutes,
    })


@student_required
def student_submit_test(request, attempt_id):
    """Test javoblarini qabul qilish va baholash."""
    if request.method != 'POST':
        return redirect('web:student_dashboard')

    student = request.user
    attempt = get_object_or_404(TestAttempt, id=attempt_id, student=student)

    if attempt.is_submitted:
        messages.warning(request, "Bu test allaqachon topshirilgan.")
        return redirect('web:student_result_detail', attempt_id=attempt.id)

    questions = attempt.topic.questions.all()
    mapping = attempt.answer_mapping

    for question in questions:
        selected = request.POST.get(f'q_{question.id}')
        if selected:
            q_map = mapping.get(str(question.id), {})
            original_selected = q_map.get(selected, selected)
            is_correct = (original_selected == question.correct_answer)
            AttemptAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_option=selected,
                is_correct=is_correct,
            )

    attempt.grade()

    return redirect('web:student_result_detail', attempt_id=attempt.id)


@student_required
def student_result_detail(request, attempt_id):
    """Bitta urinish natijasini batafsil ko'rsatish."""
    attempt = get_object_or_404(
        TestAttempt,
        id=attempt_id,
        student=request.user,
        is_submitted=True,
    )
    answers = attempt.answers.select_related('question').all()

    answers_data = []
    for answer in answers:
        q = answer.question
        q_map = attempt.answer_mapping.get(str(q.id), {})
        reverse_map = {v: k for k, v in q_map.items()}
        correct_display = reverse_map.get(q.correct_answer, q.correct_answer)
        disp_options = {}
        orig_options = {'A': q.option_a, 'B': q.option_b, 'C': q.option_c, 'D': q.option_d}
        for disp_key, orig_key in q_map.items():
            disp_options[disp_key] = orig_options.get(orig_key, '')
        answers_data.append({
            'question': q,
            'selected': answer.selected_option,
            'correct_display': correct_display,
            'is_correct': answer.is_correct,
            'displayed_options': disp_options,
        })

    return render(request, 'student/result_detail.html', {
        'attempt': attempt,
        'answers_data': answers_data,
    })


@student_required
def student_results(request):
    """O'quvchining barcha urinishlari tarixi."""
    attempts = TestAttempt.objects.filter(
        student=request.user,
        is_submitted=True,
    ).select_related('topic', 'topic__group', 'topic__group__course').order_by('-submitted_at')

    return render(request, 'student/results.html', {'attempts': attempts})
