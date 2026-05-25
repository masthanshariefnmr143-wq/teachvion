from rest_framework import serializers, generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Course, Lesson, Enrollment, VideoProgress


class LessonSerializer(serializers.ModelSerializer):
    class Meta:
        model = Lesson
        fields = ['id', 'title', 'video_url', 'order', 'duration_mins']


class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    trainer_name = serializers.SerializerMethodField()
    enrolled_count = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'category', 'price',
                  'thumbnail', 'badge', 'trainer_name', 'enrolled_count', 'lessons']

    def get_trainer_name(self, obj):
        return obj.trainer.get_full_name() if obj.trainer else ''

    def get_enrolled_count(self, obj):
        return obj.get_enrolled_count()


class CourseListAPIView(generics.ListAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Course.objects.filter(is_active=True)

    def get_queryset(self):
        qs = super().get_queryset()
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs


class CourseDetailAPIView(generics.RetrieveAPIView):
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    queryset = Course.objects.filter(is_active=True)


class CoursesWithProgressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        enrollments = Enrollment.objects.filter(
            student=request.user, payment_status='paid'
        ).select_related('course')
        data = []
        for e in enrollments:
            total = e.course.lessons.count()
            done = VideoProgress.objects.filter(
                student=request.user, lesson__course=e.course, completed=True
            ).count()
            data.append({
                'course_id': e.course.id,
                'title': e.course.title,
                'progress': int((done / total) * 100) if total else 0,
                'total_lessons': total,
                'completed_lessons': done,
            })
        return Response(data)


class UpdateProgressAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, lesson_id):
        from .models import Lesson
        lesson = generics.get_object_or_404(Lesson, id=lesson_id)
        percent = min(int(request.data.get('percent', 0)), 100)
        vp, _ = VideoProgress.objects.get_or_create(student=request.user, lesson=lesson)
        vp.watched_percent = max(vp.watched_percent, percent)
        vp.completed = vp.watched_percent >= 90
        vp.save()
        return Response({'status': 'ok', 'completed': vp.completed})