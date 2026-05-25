from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from accounts.models import CustomUser
from courses.models import Attendance, Course, Enrollment, VideoProgress, ClassTiming
from exams.models import ExamAttempt
from certificates.models import Certificate


def role_required(role):
    """Decorator: redirect if user doesn't have the required role."""
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect(f'/login/?next={request.path}')
            if request.user.role != role:
                messages.error(request, "Access denied.")
                return redirect(request.user.get_dashboard_url())
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator


# ═══════════════════════════════════════════════════════════════════
# STUDENT DASHBOARD
# ═══════════════════════════════════════════════════════════════════
@login_required
@role_required('student')
def student_dashboard_view(request):
    student = request.user

    # Enrolled courses with progress
    enrollments = Enrollment.objects.filter(
        student=student, payment_status='paid'
    ).select_related('course')

    courses_data = []
    live_class_notifications = []
    for e in enrollments:
        total = e.course.lessons.count()
        done = VideoProgress.objects.filter(
            student=student, lesson__course=e.course, completed=True
        ).count()
        pct = int((done / total) * 100) if total else 0
        latest_attempt = ExamAttempt.objects.filter(
            student=student, course=e.course
        ).order_by('-attempted_at').first()
        timings = ClassTiming.objects.filter(course=e.course)
        for t in timings:
            display_date = t.date.strftime('%a, %d %b %Y') if t.date else t.get_day_of_week_display()
            live_class_notifications.append({
                'course_title': e.course.title,
                'day': display_date,
                'time': f"{t.start_time.strftime('%H:%M')} - {t.end_time.strftime('%H:%M')}",
                'meeting_link': t.meeting_link,
            })
        courses_data.append({
            'enrollment': e,
            'course': e.course,
            'progress': pct,
            'completed_lessons': done,
            'total_lessons': total,
            'exam_attempt': latest_attempt,
            'can_take_exam': pct >= 100,
            'timings': timings,
        })

    # Certificates
    certificates = Certificate.objects.filter(student=student).select_related('course')

    # Total spent
    total_spent = enrollments.aggregate(total=Sum('amount_paid'))['total'] or 0

    # Pending payment
    pending = Enrollment.objects.filter(student=student, payment_status='pending').select_related('course')

    return render(request, 'student_dashboard.html', {
        'student': student,
        'courses_data': courses_data,
        'certificates': certificates,
        'total_spent': total_spent,
        'pending_enrollments': pending,
        'total_enrolled': enrollments.count(),
        'total_certs': certificates.count(),
        'live_class_notifications': live_class_notifications,
    })


# ═══════════════════════════════════════════════════════════════════
# TRAINER DASHBOARD
# ═══════════════════════════════════════════════════════════════════
@login_required
@role_required('trainer')
def trainer_dashboard_view(request):
    trainer = request.user
    courses = Course.objects.filter(trainer=trainer).prefetch_related('enrollments', 'lessons')

    attendance_records = Attendance.objects.filter(
        course__in=courses,
        attended=True
    ).values('course').annotate(
        record_count=Count('id'),
        student_count=Count('student', distinct=True)
    )
    attendance_by_course = {
        record['course']: record
        for record in attendance_records
    }

    courses_data = []
    for course in courses:
        enrolled_students = Enrollment.objects.filter(
            course=course, payment_status='paid'
        ).select_related('student')

        students_with_progress = []
        for e in enrolled_students:
            total = course.lessons.count()
            done = VideoProgress.objects.filter(
                student=e.student, lesson__course=course, completed=True
            ).count()
            pct = int((done / total) * 100) if total else 0
            attempt = ExamAttempt.objects.filter(
                student=e.student, course=course
            ).order_by('-attempted_at').first()
            students_with_progress.append({
                'student': e.student,
                'progress': pct,
                'exam_attempt': attempt,
                'enrolled_at': e.enrolled_at,
            })

        timings = ClassTiming.objects.filter(course=course, trainer=trainer)
        attendance_info = attendance_by_course.get(course.id, {
            'record_count': 0,
            'student_count': 0,
        })
        courses_data.append({
            'course': course,
            'students': students_with_progress,
            'student_count': len(students_with_progress),
            'lesson_count': course.lessons.count(),
            'timings': timings,
            'attendance_count': attendance_info['record_count'],
            'attendance_students': attendance_info['student_count'],
        })

    return render(request, 'trainer_dashboard.html', {
        'trainer': trainer,
        'courses_data': courses_data,
        'total_courses': len(courses_data),
        'total_students': sum(c['student_count'] for c in courses_data),
        'total_lessons': sum(c['lesson_count'] for c in courses_data),
        'total_live_classes': sum(len(c['timings']) for c in courses_data),
    })


# ═══════════════════════════════════════════════════════════════════
# ADMIN DASHBOARD
# ═══════════════════════════════════════════════════════════════════
@login_required
@role_required('admin')
def admin_dashboard_view(request):
    # Stats
    total_students = CustomUser.objects.filter(role='student').count()
    total_trainers = CustomUser.objects.filter(role='trainer').count()
    total_courses = Course.objects.filter(is_active=True).count()
    total_revenue = Enrollment.objects.filter(payment_status='paid').aggregate(
        total=Sum('amount_paid')
    )['total'] or 0
    total_certificates = Certificate.objects.count()
    total_enrollments = Enrollment.objects.filter(payment_status='paid').count()
    total_attendance = Attendance.objects.filter(attended=True).count()

    # Recent enrollments (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_enrollments = Enrollment.objects.filter(
        payment_status='paid', enrolled_at__gte=thirty_days_ago
    ).select_related('student', 'course').order_by('-enrolled_at')[:10]

    # Monthly revenue for chart (last 6 months)
    monthly_revenue = []
    for i in range(5, -1, -1):
        month_start = (timezone.now().replace(day=1) - timedelta(days=30 * i))
        month_end = (month_start + timedelta(days=32)).replace(day=1)
        rev = Enrollment.objects.filter(
            payment_status='paid',
            enrolled_at__gte=month_start,
            enrolled_at__lt=month_end
        ).aggregate(total=Sum('amount_paid'))['total'] or 0
        monthly_revenue.append({
            'month': month_start.strftime('%b %Y'),
            'revenue': float(rev),
        })

    # All students, trainers, courses
    students = CustomUser.objects.filter(role='student').order_by('-date_joined')
    trainers = CustomUser.objects.filter(role='trainer').order_by('-date_joined')
    courses  = Course.objects.all().select_related('trainer').prefetch_related('enrollments')

    # Per-trainer stats: assigned courses + student count
    trainers_data = []
    for t in trainers:
        assigned      = Course.objects.filter(trainer=t, is_active=True)
        student_count = Enrollment.objects.filter(
            course__trainer=t, payment_status='paid'
        ).values('student').distinct().count()
        trainers_data.append({
            'trainer':       t,
            'assigned':      assigned,
            'course_count':  assigned.count(),
            'student_count': student_count,
        })

    attendance_data = Attendance.objects.filter(attended=True).values('course').annotate(
        record_count=Count('id')
    )
    attendance_map = {item['course']: item['record_count'] for item in attendance_data}
    for c in courses:
        c.attendance_count = attendance_map.get(c.id, 0)

    return render(request, 'admin_dashboard.html', {
        'total_students':     total_students,
        'total_trainers':     total_trainers,
        'total_courses':      total_courses,
        'total_revenue':      total_revenue,
        'total_certificates': total_certificates,
        'total_enrollments':  total_enrollments,
        'total_attendance':   total_attendance,
        'recent_enrollments': recent_enrollments,
        'monthly_revenue':    monthly_revenue,
        'students':           students,
        'trainers':           trainers,
        'trainers_data':      trainers_data,
        'courses':            courses,
        'all_trainers':       trainers,
    })


# ─── Admin: CRUD Students ─────────────────────────────────────────
@login_required
@role_required('admin')
def admin_student_edit_view(request, user_id):
    student = get_object_or_404(CustomUser, id=user_id, role='student')
    if request.method == 'POST':
        student.first_name = request.POST.get('first_name', student.first_name)
        student.last_name = request.POST.get('last_name', student.last_name)
        student.phone = request.POST.get('phone', student.phone)
        student.is_active = request.POST.get('is_active') == 'on'
        student.save()
        messages.success(request, "Student updated.")
        return redirect('admin_dashboard')
    return render(request, 'edit_user.html', {'user_obj': student})


@login_required
@role_required('admin')
def admin_user_delete_view(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    if user.role == 'admin':
        messages.error(request, "Cannot delete admin accounts.")
        return redirect('admin_dashboard')
    user.is_active = False   # soft delete
    user.save()
    messages.success(request, f"{user.get_full_name()} deactivated.")
    return redirect('admin_dashboard')


# ─── Admin: CRUD Courses ──────────────────────────────────────────
@login_required
@role_required('admin')
def admin_course_create_view(request):
    from courses.forms import CourseForm
    form = CourseForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Course created.")
        return redirect('admin_dashboard')
    return render(request, 'course_form.html', {'form': form, 'action': 'Create'})


@login_required
@role_required('admin')
def admin_course_edit_view(request, course_id):
    from courses.forms import CourseForm
    course = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, request.FILES or None, instance=course)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Course updated.")
        return redirect('admin_dashboard')
    return render(request, 'course_form.html', {'form': form, 'action': 'Edit'})


@login_required
@role_required('admin')
def admin_course_delete_view(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    course.is_active = False
    course.save()
    messages.success(request, "Course deactivated.")
    return redirect('admin_dashboard')


# ─── Admin: Assign Trainer to Course ─────────────────────────────
@login_required
@role_required('admin')
def admin_assign_trainer_view(request, course_id):
    from django.http import JsonResponse
    if request.method == 'POST':
        course     = get_object_or_404(Course, id=course_id)
        trainer_id = request.POST.get('trainer_id')
        if trainer_id:
            trainer = get_object_or_404(CustomUser, id=trainer_id, role='trainer')
            course.trainer = trainer
            course.save()
            messages.success(request, f"Trainer '{trainer.get_full_name()}' assigned to '{course.title}'.")
        else:
            course.trainer = None
            course.save()
            messages.success(request, f"Trainer removed from '{course.title}'.")
        return redirect('admin_dashboard')
    return redirect('admin_dashboard')