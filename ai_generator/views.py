"""
AI Question Generator.

Uses OpenAI GPT (or any LLM API) to automatically generate MCQ questions
from a topic's text content.

Usage:
    POST /api/v1/ai/generate-questions/
    Body: { "topic_id": 5, "count": 5 }

    The AI reads the topic's content and generates {count} MCQ questions.
    Each question has 4 options and one correct answer.

Setup:
    1. Add OPENAI_API_KEY to your .env file
    2. pip install openai

Note: This requires an OpenAI API key. Without it, the endpoint
      returns an error with instructions.
"""

import json
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from tests_app.models import Topic, Question
from users.permissions import IsTeacher


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsTeacher])
def generate_questions_view(request):
    """
    POST /api/v1/ai/generate-questions/

    Request body:
        {
            "topic_id": 5,
            "count": 5        ← how many questions to generate (default: 5)
        }

    Response:
        List of generated questions saved to the database.

    How it works:
        1. Reads the topic's title and content
        2. Sends it to OpenAI with a structured prompt
        3. Parses the AI response
        4. Creates Question objects in the database
        5. Returns the created questions

    If OPENAI_API_KEY is not configured, returns a helpful error.
    """
    topic_id = request.data.get('topic_id')
    count = request.data.get('count', 5)

    if not topic_id:
        return Response({'error': 'topic_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        topic = Topic.objects.get(pk=topic_id)
    except Topic.DoesNotExist:
        return Response({'error': 'Topic not found.'}, status=status.HTTP_404_NOT_FOUND)

    if not topic.content:
        return Response(
            {'error': 'Topic has no content. Add content to the topic first.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Try to import OpenAI
    try:
        from openai import OpenAI
        import os
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("No API key")
        client = OpenAI(api_key=api_key)
    except (ImportError, ValueError):
        return Response(
            {
                'error': 'AI feature not configured.',
                'instructions': (
                    '1. pip install openai\n'
                    '2. Add OPENAI_API_KEY=sk-... to your .env file\n'
                    '3. Try again.'
                )
            },
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
        )

    # Build the prompt
    prompt = f"""You are an educational test creator. Based on the following topic, 
generate exactly {count} multiple-choice questions (MCQ).

Topic Title: {topic.title}
Topic Content: {topic.content}

Rules:
- Each question must have exactly 4 options (A, B, C, D)
- Only one option is correct
- Questions should test understanding, not just memorization
- Make distractors (wrong answers) plausible but clearly wrong

Return ONLY a valid JSON array in this exact format:
[
  {{
    "question_text": "What is ...?",
    "option_a": "First option",
    "option_b": "Second option", 
    "option_c": "Third option",
    "option_d": "Fourth option",
    "correct_answer": "A"
  }}
]

Generate {count} questions now:"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "You are an expert educational content creator. Always return valid JSON only, no explanations."
                },
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )

        raw_content = response.choices[0].message.content.strip()

        # Clean markdown code blocks if present
        if raw_content.startswith('```'):
            raw_content = raw_content.split('```')[1]
            if raw_content.startswith('json'):
                raw_content = raw_content[4:]

        questions_data = json.loads(raw_content)

    except json.JSONDecodeError:
        return Response(
            {'error': 'AI returned invalid JSON. Please try again.'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    except Exception as e:
        return Response(
            {'error': f'AI API error: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    # Save generated questions to database
    created_questions = []
    start_order = topic.questions.count()

    for i, q_data in enumerate(questions_data):
        try:
            question = Question.objects.create(
                topic=topic,
                question_text=q_data['question_text'],
                option_a=q_data['option_a'],
                option_b=q_data['option_b'],
                option_c=q_data['option_c'],
                option_d=q_data['option_d'],
                correct_answer=q_data['correct_answer'].upper(),
                order_index=start_order + i + 1,
            )
            created_questions.append({
                'id': question.id,
                'question_text': question.question_text,
                'option_a': question.option_a,
                'option_b': question.option_b,
                'option_c': question.option_c,
                'option_d': question.option_d,
                'correct_answer': question.correct_answer,
            })
        except Exception as e:
            continue

    return Response({
        'message': f'Successfully generated {len(created_questions)} questions for "{topic.title}".',
        'questions': created_questions,
    }, status=status.HTTP_201_CREATED)
