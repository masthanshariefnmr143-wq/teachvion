from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum
from accounts.models import CustomUser
from courses.models import Course, Enrollment, VideoProgress
from exams.models import ExamAttempt
from certificates.models import Certificate


class DashboardSummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user

        if user.role == 'student':
            enrollments = Enrollment.objects.filter(student=user, payment_status='paid')
            attempts = ExamAttempt.objects.filter(student=user)
            certs = Certificate.objects.filter(student=user)
            return Response({
                'role': 'student',
                'total_courses': enrollments.count(),
                'total_spent': float(enrollments.aggregate(t=Sum('amount_paid'))['t'] or 0),
                'total_certs': certs.count(),
                'passed_exams': attempts.filter(passed=True).count(),
            })

        elif user.role == 'trainer':
            courses = Course.objects.filter(trainer=user)
            students = Enrollment.objects.filter(course__in=courses, payment_status='paid')
            return Response({
                'role': 'trainer',
                'total_courses': courses.count(),
                'total_students': students.count(),
            })

        elif user.role == 'admin':
            return Response({
                'role': 'admin',
                'total_students': CustomUser.objects.filter(role='student').count(),
                'total_trainers': CustomUser.objects.filter(role='trainer').count(),
                'total_courses': Course.objects.filter(is_active=True).count(),
                'total_revenue': float(
                    Enrollment.objects.filter(payment_status='paid').aggregate(
                        t=Sum('amount_paid')
                    )['t'] or 0
                ),
            })