from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from courses.models import Course, Enrollment, VideoProgress
from .models import Question, ExamAttempt, ExamAnswer
from certificates.models import Certificate
from courses.models import PartnerCompany  # imported from courses


@login_required
def exam_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    # Must be enrolled and paid
    enrollment = Enrollment.objects.filter(
        student=request.user, course=course, payment_status='paid'
    ).first()
    if not enrollment:
        messages.error(request, "You must be enrolled to take the exam.")
        return redirect('index')

    # Must have completed all lessons (>=90% each)
    total_lessons = course.lessons.count()
    completed = VideoProgress.objects.filter(
        student=request.user, lesson__course=course, completed=True
    ).count()
    if total_lessons > 0 and completed < total_lessons:
        messages.error(request, f"Complete all lessons first ({completed}/{total_lessons} done).")
        return redirect('course_player', course_id=course.id)

    questions = Question.objects.filter(course=course)

    if request.method == 'POST':
        score = 0
        attempt = ExamAttempt.objects.create(
            student=request.user,
            course=course,
            total_questions=questions.count(),
        )
        for q in questions:
            selected = request.POST.get(f'q_{q.id}', '')
            is_correct = (selected == q.correct_option)
            if is_correct:
                score += 1
            ExamAnswer.objects.create(
                attempt=attempt,
                question=q,
                selected_option=selected,
                is_correct=is_correct,
            )

        total = questions.count()
        percentage = (score / total * 100) if total else 0
        attempt.score = score
        attempt.percentage = percentage
        attempt.passed = percentage >= 50
        attempt.eligible_for_partner = percentage >= 70
        attempt.save()

        return redirect('exam_result', attempt_id=attempt.id)

    return render(request, 'exam.html', {
        'course': course, 'questions': questions
    })


@login_required
def exam_result_view(request, attempt_id):
    attempt = get_object_or_404(ExamAttempt, id=attempt_id, student=request.user)
    course = attempt.course

    # Auto-create certificate if passed
    certificate = None
    if attempt.passed:
        certificate, _ = Certificate.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'exam_attempt': attempt}
        )

    # Partner companies if >=70%
    partner_companies = []
    if attempt.eligible_for_partner:
        try:
            from courses.models import PartnerCompany
            partner_companies = PartnerCompany.objects.filter(
                courses=course, min_score_required__lte=attempt.percentage
            )
        except Exception:
            pass

    return render(request, 'exam_result.html', {
        'attempt': attempt,
        'course': course,
        'certificate': certificate,
        'partner_companies': partner_companies,
        'answers': attempt.answers.select_related('question').all(),
    })


@login_required
def exam_hub_view(request):
    """All exams page (existing exam.html)"""
    courses = Course.objects.filter(is_active=True)
    my_attempts = {}
    if request.user.is_authenticated and request.user.role == 'student':
        for a in ExamAttempt.objects.filter(student=request.user):
            my_attempts[a.course_id] = a
    return render(request, 'exam_hub.html', {
        'courses': courses, 'my_attempts': my_attempts
    })