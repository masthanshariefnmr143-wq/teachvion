from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, serializers
from django.shortcuts import get_object_or_404
from courses.models import Course, Enrollment
from .models import Question, ExamAttempt, ExamAnswer
from certificates.models import Certificate


class ExamQuestionsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        questions = Question.objects.filter(course=course)
        data = {
            'course_id': course.id,
            'course_name': course.title,
            'questions': [
                {
                    'id': q.id,
                    'text': q.text,
                    'options': {
                        'a': q.option_a, 'b': q.option_b,
                        'c': q.option_c, 'd': q.option_d,
                    }
                } for q in questions
            ]
        }
        return Response(data)


class ExamSubmitAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if not request.user.is_authenticated:
            return Response({
                'status': 'login_required',
                'login_url': '/login/'
            })

        course_id = request.data.get('course_id')
        answers_data = request.data.get('answers', {})

        course = get_object_or_404(Course, id=course_id)
        questions = Question.objects.filter(course=course)

        score = 0
        attempt = ExamAttempt.objects.create(
            student=request.user,
            course=course,
            total_questions=questions.count(),
        )

        for q in questions:
            selected = answers_data.get(str(q.id), '')
            is_correct = (selected == q.correct_option)
            if is_correct:
                score += 1
            ExamAnswer.objects.create(
                attempt=attempt, question=q,
                selected_option=selected, is_correct=is_correct,
            )

        total = questions.count()
        pct = (score / total * 100) if total else 0
        attempt.score = score
        attempt.percentage = pct
        attempt.passed = pct >= 50
        attempt.eligible_for_partner = pct >= 70
        attempt.save()

        # Auto-create certificate if passed
        if attempt.passed:
            Certificate.objects.get_or_create(
                student=request.user, course=course,
                defaults={'exam_attempt': attempt}
            )

        return Response({
            'status': 'success',
            'score': score,
            'total': total,
            'percentage': round(pct, 1),
            'passed': attempt.passed,
            'eligible_for_partner': attempt.eligible_for_partner,
            'message': (
                f"You scored {score}/{total} ({pct:.1f}%). "
                + ("Congratulations! Certificate issued." if attempt.passed
                   else "You need 50% to pass. Try again!")
            )
        })


class ExamResultsAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        attempts = ExamAttempt.objects.filter(student=request.user).select_related('course')
        return Response([{
            'attempt_id': a.id,
            'course': a.course.title,
            'score': a.score,
            'total': a.total_questions,
            'percentage': a.percentage,
            'passed': a.passed,
            'attempted_at': a.attempted_at,
        } for a in attempts])


class ExamResultDetailAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, attempt_id):
        attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)
        return Response({
            'attempt_id': attempt.id,
            'course': attempt.course.title,
            'score': attempt.score,
            'total': attempt.total_questions,
            'percentage': attempt.percentage,
            'passed': attempt.passed,
            'eligible_for_partner': attempt.eligible_for_partner,
        })


class ExamProgressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        attempts = ExamAttempt.objects.filter(student=request.user)
        return Response([{
            'course_id': a.course_id,
            'course': a.course.title,
            'best_score': a.percentage,
            'passed': a.passed,
        } for a in attempts])