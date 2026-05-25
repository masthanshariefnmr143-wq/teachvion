import hmac
import hashlib
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from .models import Course, Lesson, Enrollment, VideoProgress, ClassTiming, Attendance
from .forms import LessonUploadForm, ClassTimingForm, normalize_video_url
from accounts.models import CustomUser

ATTENDANCE_THRESHOLD = 70

# ─── Home / Course listing ────────────────────────────────────────
def index_view(request):
    courses = Course.objects.filter(is_active=True).select_related('trainer')
    return render(request, 'index.html', {'courses': courses})


# ─── Single course detail ─────────────────────────────────────────
def course_detail_view(request, course_id):
    course = get_object_or_404(Course, id=course_id, is_active=True)
    lessons = course.lessons.all()
    enrolled = False
    if request.user.is_authenticated:
        enrolled = Enrollment.objects.filter(
            student=request.user, course=course, payment_status='paid'
        ).exists()
    return render(request, 'course_details.html', {
        'course': course, 'lessons': lessons, 'enrolled': enrolled
    })


# ─── Enroll endpoint (AJAX) ───────────────────────────────────────
# NO @login_required here — we handle it manually to return JSON not a redirect
def enroll_view(request, course_id):
    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest'

    # 1. Not logged in
    if not request.user.is_authenticated:
        if is_ajax:
            return JsonResponse({
                'status': 'login_required',
                'login_url': f'/login/?next=/enroll/{course_id}/',
            })
        return redirect(f'/login/?next=/enroll/{course_id}/')

    # 2. Only students can enroll
    if request.user.role != 'student':
        if is_ajax:
            return JsonResponse({
                'status': 'error',
                'message': 'Only students can enroll.',
            })
        messages.error(request, 'Only students can enroll.')
        return redirect('index')

    course = get_object_or_404(Course, id=course_id)

    # 3. Already enrolled and paid
    enrollment = Enrollment.objects.filter(
        student=request.user, course=course
    ).first()

    if enrollment and enrollment.payment_status == 'paid':
        if is_ajax:
            return JsonResponse({
                'status': 'already_enrolled',
                'player_url': f'/course/{course.id}/player/',
            })
        return redirect('course_player', course_id=course.id)

    # 4. Create enrollment record if not exists
    if not enrollment:
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            payment_status='pending',
        )

    # 5. Use UPI/manual payment flow — create enrollment and send payment page URL
    enrollment.save()
    if is_ajax:
        return JsonResponse({
            'status': 'payment_required',
            'enrollment_id': enrollment.id,
            'payment_url': f'/payment/{enrollment.id}/',
            'amount': int(float(course.price) * 100),
            'course_title': course.title,
        })
    return redirect('payment', enrollment_id=enrollment.id)


# ─── Payment page ─────────────────────────────────────────────────
@login_required
def payment_view(request, enrollment_id):
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=request.user)
    if enrollment.payment_status == 'paid':
        return redirect('course_player', course_id=enrollment.course.id)
    # Provide UPI info so the template can show UPI as the default method
    return render(request, 'payment.html', {
        'enrollment': enrollment,
        'course': enrollment.course,
        'razorpay_key': '',  # disable razorpay by default for UPI flow
        'upi_vpa': getattr(settings, 'UPI_VPA', ''),
        'upi_qr': getattr(settings, 'UPI_QR_URL', ''),
        'upi_name': getattr(settings, 'UPI_ACCOUNT_NAME', ''),
        'force_upi': True,
    })


# ─── Razorpay webhook / payment verify ────────────────────────────
@csrf_exempt
@require_POST
def payment_verify_view(request):
    import json
    data = json.loads(request.body)
    razorpay_order_id   = data.get('razorpay_order_id')
    razorpay_payment_id = data.get('razorpay_payment_id')
    razorpay_signature  = data.get('razorpay_signature')

    msg = f"{razorpay_order_id}|{razorpay_payment_id}"
    generated_sig = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode(),
        msg.encode(), hashlib.sha256
    ).hexdigest()

    if generated_sig == razorpay_signature:
        try:
            enrollment = Enrollment.objects.get(razorpay_order_id=razorpay_order_id)
            enrollment.payment_status   = 'paid'
            enrollment.razorpay_payment_id = razorpay_payment_id
            enrollment.amount_paid      = enrollment.course.price
            enrollment.save()
            return JsonResponse({
                'status': 'success',
                'redirect': f'/course/{enrollment.course.id}/player/'
            })
        except Enrollment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Enrollment not found'}, status=404)
    return JsonResponse({'status': 'error', 'message': 'Signature mismatch'}, status=400)


# ─── Manual payment confirm (no Razorpay) ────────────────────────
@login_required
@require_POST
def payment_confirm_view(request, enrollment_id):
    """For demo/testing without real Razorpay — marks enrollment as paid."""
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=request.user)
    enrollment.payment_status = 'paid'
    enrollment.amount_paid    = enrollment.course.price
    enrollment.save()
    return JsonResponse({
        'ok': True,
        'player_url': f'/course/{enrollment.course.id}/player/',
    })


# ─── Course Player ────────────────────────────────────────────────
@login_required
def course_player_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    enrollment = Enrollment.objects.filter(
        student=request.user, course=course, payment_status='paid'
    ).first()
    if not enrollment:
        messages.error(request, "Please enroll to access this course.")
        return redirect('index')

    lessons       = course.lessons.all()
    lesson_id     = request.GET.get('lesson')
    if lesson_id:
        current_lesson = get_object_or_404(Lesson, id=lesson_id, course=course)
    else:
        # Prefer the first lesson that has a video (file or URL), otherwise fallback to first lesson
        current_lesson = None
        for l in lessons:
            if l.video_file or l.video_url:
                current_lesson = l
                break
        if not current_lesson:
            current_lesson = lessons.first()

    if current_lesson:
        if current_lesson.video_url:
            normalized = normalize_video_url(current_lesson.video_url)
            if normalized:
                current_lesson.video_url = normalized
            else:
                # If the stored URL is not a valid embed source, fall back to uploaded file if present.
                current_lesson.video_url = ''

    progress_map = {
        vp.lesson_id: vp
        for vp in VideoProgress.objects.filter(
            student=request.user, lesson__course=course
        )
    }

    total      = lessons.count()
    completed  = sum(1 for l in lessons
                     if progress_map.get(l.id) and progress_map[l.id].completed)
    completion_pct = int((completed / total) * 100) if total else 0
    can_take_exam  = completion_pct >= 100

    return render(request, 'course_player.html', {
        'course': course,
        'lessons': lessons,
        'current_lesson': current_lesson,
        'progress_map': progress_map,
        'completion_pct': completion_pct,
        'can_take_exam': can_take_exam,
        'enrollment': enrollment,
    })


# ─── Update Video Progress (AJAX) ────────────────────────────────
@login_required
@require_POST
def update_progress_view(request, lesson_id):
    import json
    lesson  = get_object_or_404(Lesson, id=lesson_id)
    data    = json.loads(request.body)
    percent = min(int(data.get('percent', 0)), 100)

    vp, _              = VideoProgress.objects.get_or_create(student=request.user, lesson=lesson)
    vp.watched_percent = max(vp.watched_percent, percent)
    vp.completed       = vp.watched_percent >= 90
    vp.save()

    return JsonResponse({'status': 'ok', 'completed': vp.completed, 'percent': vp.watched_percent})


# ─── My Courses (student) ─────────────────────────────────────────
@login_required
def my_courses_view(request):
    enrollments = Enrollment.objects.filter(
        student=request.user, payment_status='paid'
    ).select_related('course')

    courses_with_progress = []
    for e in enrollments:
        total     = e.course.lessons.count()
        completed = VideoProgress.objects.filter(
            student=request.user, lesson__course=e.course, completed=True
        ).count()
        pct = int((completed / total) * 100) if total else 0
        courses_with_progress.append({
            'enrollment': e,
            'course': e.course,
            'progress': pct,
            'completed_lessons': completed,
            'total_lessons': total,
        })

    return render(request, 'my_courses.html', {'courses': courses_with_progress})


# ─── Trainer: Upload Lesson ───────────────────────────────────────
@login_required
def upload_lesson_view(request, course_id):
    if request.user.role != 'trainer':
        messages.error(request, "Access denied.")
        return redirect('index')

    course = get_object_or_404(Course, id=course_id, trainer=request.user)
    form   = LessonUploadForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        lesson        = form.save(commit=False)
        lesson.course = course
        lesson.save()
        messages.success(request, "Lesson uploaded successfully.")
        return redirect('upload_lesson', course_id=course.id)

    lessons = course.lessons.all()
    return render(request, 'upload_lesson.html', {
        'form': form, 'course': course, 'lessons': lessons
    })


# ─── Trainer: Delete Lesson ───────────────────────────────────────
@login_required
def delete_lesson_view(request, lesson_id):
    lesson    = get_object_or_404(Lesson, id=lesson_id, course__trainer=request.user)
    course_id = lesson.course.id
    lesson.delete()
    messages.success(request, "Lesson deleted.")
    return redirect('upload_lesson', course_id=course_id)


# ─── Trainer: Class Timings ───────────────────────────────────────
@login_required
def class_timings_view(request, course_id):
    if request.user.role != 'trainer':
        return redirect('index')
    course = get_object_or_404(Course, id=course_id, trainer=request.user)
    form   = ClassTimingForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        timing         = form.save(commit=False)
        timing.trainer = request.user
        timing.course  = course
        timing.save()

        # Notify paid enrolled students about the new live class timing
        enrolled_students = Enrollment.objects.filter(
            course=course, payment_status='paid'
        ).select_related('student')

        recipient_list = [e.student.email for e in enrolled_students if e.student.email]
        if recipient_list:
            subject = f"New live class scheduled for {course.title}"
            message = (
                f"Hello,\n\n"
                f"A new live class has been scheduled for your course '{course.title}'.\n"
                f"Date: {timing.date.strftime('%a, %d %b %Y') if timing.date else timing.get_day_of_week_display()}\n"
                f"Time: {timing.start_time.strftime('%H:%M')} - {timing.end_time.strftime('%H:%M')}\n"
            )
            if timing.meeting_link:
                message += f"Meeting link: {timing.meeting_link}\n"
            if timing.notes:
                message += f"Notes: {timing.notes}\n"
            message += "\nPlease join the session on time.\n\nThanks,\nTeachvion Team"

            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=True,
            )

        messages.success(request, "Class timing saved.")
        return redirect('class_timings', course_id=course.id)

    timings = ClassTiming.objects.filter(course=course, trainer=request.user)
    return render(request, 'class_timings.html', {
        'form': form, 'course': course, 'timings': timings
    })


@login_required
def class_attendance_view(request, course_id, timing_id):
    if request.user.role != 'trainer':
        return redirect('index')

    course = get_object_or_404(Course, id=course_id, trainer=request.user)
    timing = get_object_or_404(ClassTiming, id=timing_id, course=course, trainer=request.user)

    enrolled_students = CustomUser.objects.filter(
        enrollments__course=course,
        enrollments__payment_status='paid'
    ).distinct()

    if request.method == 'POST':
        for student in enrolled_students:
            percent_value = request.POST.get(f'attendance_{student.id}', '0')
            try:
                percent = int(percent_value)
            except (TypeError, ValueError):
                percent = 0
            percent = max(0, min(percent, 100))
            Attendance.objects.update_or_create(
                student=student,
                course=course,
                class_timing=timing,
                defaults={
                    'attendance_percent': percent,
                    'attended': percent >= ATTENDANCE_THRESHOLD,
                }
            )
        messages.success(request, "Attendance saved successfully.")
        return redirect('class_attendance', course_id=course.id, timing_id=timing.id)

    attendance_data = Attendance.objects.filter(class_timing=timing).values(
        'student_id', 'attended', 'attendance_percent'
    )
    attendance_records = {item['student_id']: item for item in attendance_data}
    attendance_percent_map = {
        item['student_id']: item['attendance_percent'] for item in attendance_data
    }
    attended_count = sum(1 for item in attendance_data if item['attended'])
    present_student_ids = [item['student_id'] for item in attendance_data if item['attended']]

    return render(request, 'attendance.html', {
        'course': course,
        'timing': timing,
        'students': enrolled_students,
        'attendance_records': attendance_records,
        'attendance_percent_map': attendance_percent_map,
        'present_student_ids': present_student_ids,
        'attended_count': attended_count,
        'attendance_threshold': ATTENDANCE_THRESHOLD,
    })


# ─── Category pages ───────────────────────────────────────────────
def category_view(request, category):
    courses = Course.objects.filter(category=category, is_active=True)
    return render(request, 'category.html', {
        'courses': courses, 'category': category
    })

# testinomials
