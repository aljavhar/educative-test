"""
Management command to seed the database with demo data.

Run with:
    python manage.py seed_data

This creates:
  - 1 teacher account
  - 3 student accounts
  - 2 courses (Math, Python Programming)
  - 2 groups
  - 2 topics with questions
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import date


class Command(BaseCommand):
    help = 'Seed the database with demo data for testing'

    def handle(self, *args, **options):
        from users.models import User
        from courses.models import Course, Group
        from tests_app.models import Topic, Question

        self.stdout.write('Seeding demo data...')

        # ─── 1. Create teacher ────────────────────────────────────────────────
        teacher, _ = User.objects.get_or_create(
            username='teacher',
            defaults={
                'full_name': 'Mr. John Smith',
                'email': 'teacher@example.com',
                'role': 'teacher',
                'is_staff': True,
            }
        )
        teacher.set_password('teacher123')
        teacher.save()
        self.stdout.write(self.style.SUCCESS('  ✓ Teacher: username=teacher, password=teacher123'))

        # ─── 2. Create courses ────────────────────────────────────────────────
        math_course, _ = Course.objects.get_or_create(
            name='Mathematics',
            defaults={'description': 'Algebra, Geometry, and Calculus', 'created_by': teacher}
        )
        python_course, _ = Course.objects.get_or_create(
            name='Python Programming',
            defaults={'description': 'From basics to advanced Python', 'created_by': teacher}
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Courses created'))

        # ─── 3. Create groups ────────────────────────────────────────────────
        math_group, _ = Group.objects.get_or_create(
            name='Math Group A',
            course=math_course,
            defaults={'created_by': teacher}
        )
        python_group, _ = Group.objects.get_or_create(
            name='Python Class 1',
            course=python_course,
            defaults={'created_by': teacher}
        )
        self.stdout.write(self.style.SUCCESS('  ✓ Groups created'))

        # ─── 4. Create students ────────────────────────────────────────────────
        students_data = [
            {'username': 'ali', 'full_name': 'Ali Karimov', 'group': math_group},
            {'username': 'fatima', 'full_name': 'Fatima Yusupova', 'group': math_group},
            {'username': 'sardor', 'full_name': 'Sardor Toshmatov', 'group': python_group},
        ]

        for s in students_data:
            student, _ = User.objects.get_or_create(
                username=s['username'],
                defaults={
                    'full_name': s['full_name'],
                    'role': 'student',
                    'group': s['group'],
                }
            )
            student.set_password('student123')
            student.save()

        self.stdout.write(
            self.style.SUCCESS('  ✓ Students: ali, fatima, sardor | password=student123')
        )

        # ─── 5. Create today's topic for Math group ────────────────────────────
        today = date.today()
        math_topic, _ = Topic.objects.get_or_create(
            title='Linear Equations',
            group=math_group,
            date=today,
            defaults={
                'content': 'A linear equation is an equation that forms a straight line when graphed. '
                           'The standard form is ax + b = c where a, b, c are constants and x is the variable. '
                           'To solve: isolate x by performing the same operation on both sides.',
                'passing_score': 70,
                'max_attempts': 2,
                'time_limit_minutes': 15,
                'created_by': teacher,
            }
        )

        # Add questions if none exist
        if not math_topic.questions.exists():
            questions = [
                {
                    'question_text': 'What does the equation 2x + 4 = 10 solve to?',
                    'option_a': 'x = 2',
                    'option_b': 'x = 3',
                    'option_c': 'x = 4',
                    'option_d': 'x = 7',
                    'correct_answer': 'B',
                    'order_index': 1,
                },
                {
                    'question_text': 'Which of the following is a linear equation?',
                    'option_a': 'x² + 2x = 5',
                    'option_b': '3x + 1 = 7',
                    'option_c': 'x³ = 8',
                    'option_d': '√x = 4',
                    'correct_answer': 'B',
                    'order_index': 2,
                },
                {
                    'question_text': 'If 5x - 15 = 0, what is x?',
                    'option_a': 'x = 0',
                    'option_b': 'x = 5',
                    'option_c': 'x = 3',
                    'option_d': 'x = 15',
                    'correct_answer': 'C',
                    'order_index': 3,
                },
                {
                    'question_text': 'What is the slope in the equation y = 3x + 2?',
                    'option_a': '2',
                    'option_b': '3x',
                    'option_c': '3',
                    'option_d': '5',
                    'correct_answer': 'C',
                    'order_index': 4,
                },
                {
                    'question_text': 'Solve: x/4 = 5',
                    'option_a': 'x = 1.25',
                    'option_b': 'x = 9',
                    'option_c': 'x = 20',
                    'option_d': 'x = 4/5',
                    'correct_answer': 'C',
                    'order_index': 5,
                },
            ]
            for q_data in questions:
                Question.objects.create(topic=math_topic, **q_data)

        self.stdout.write(self.style.SUCCESS('  ✓ Math topic + 5 questions created for today'))

        # ─── 6. Create Python topic ────────────────────────────────────────────
        python_topic, _ = Topic.objects.get_or_create(
            title='Python Functions',
            group=python_group,
            date=today,
            defaults={
                'content': 'A function in Python is a block of reusable code. '
                           'Defined with the "def" keyword. '
                           'Can accept parameters and return values using the "return" keyword. '
                           'Functions help organize code and avoid repetition.',
                'passing_score': 60,
                'max_attempts': 3,
                'time_limit_minutes': 20,
                'created_by': teacher,
            }
        )

        if not python_topic.questions.exists():
            py_questions = [
                {
                    'question_text': 'Which keyword is used to define a function in Python?',
                    'option_a': 'function',
                    'option_b': 'def',
                    'option_c': 'func',
                    'option_d': 'define',
                    'correct_answer': 'B',
                    'order_index': 1,
                },
                {
                    'question_text': 'What keyword returns a value from a function?',
                    'option_a': 'output',
                    'option_b': 'send',
                    'option_c': 'return',
                    'option_d': 'yield',
                    'correct_answer': 'C',
                    'order_index': 2,
                },
                {
                    'question_text': 'What is the output of: print(len("hello"))?',
                    'option_a': '4',
                    'option_b': '5',
                    'option_c': '6',
                    'option_d': 'Error',
                    'correct_answer': 'B',
                    'order_index': 3,
                },
                {
                    'question_text': 'Which is a correct way to call a function named "greet"?',
                    'option_a': 'call greet()',
                    'option_b': 'greet[]',
                    'option_c': 'greet()',
                    'option_d': 'run greet',
                    'correct_answer': 'C',
                    'order_index': 4,
                },
                {
                    'question_text': 'What does DRY stand for in programming?',
                    'option_a': "Don't Repeat Yourself",
                    'option_b': 'Do Repeat Yourself',
                    'option_c': 'Data Read Yesterday',
                    'option_d': 'Dynamic Runtime Yields',
                    'correct_answer': 'A',
                    'order_index': 5,
                },
            ]
            for q_data in py_questions:
                Question.objects.create(topic=python_topic, **q_data)

        self.stdout.write(self.style.SUCCESS('  ✓ Python topic + 5 questions created for today'))

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('✅ Demo data seeded successfully!'))
        self.stdout.write('')
        self.stdout.write('Login credentials:')
        self.stdout.write('  Teacher:  username=teacher  password=teacher123')
        self.stdout.write('  Student1: username=ali      password=student123 (Math group)')
        self.stdout.write('  Student2: username=fatima   password=student123 (Math group)')
        self.stdout.write('  Student3: username=sardor   password=student123 (Python group)')
