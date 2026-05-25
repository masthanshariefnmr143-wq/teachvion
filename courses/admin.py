from django.contrib import admin
from .models import Course, Lesson, Enrollment, VideoProgress, ClassTiming, PartnerCompany


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'trainer', 'price', 'is_active', 'created_at']
    list_filter = ['category', 'is_active']
    search_fields = ['title', 'trainer__email']
    list_editable = ['is_active', 'price']


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'order', 'duration_mins']
    list_filter = ['course']
    ordering = ['course', 'order']


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'payment_status', 'amount_paid', 'enrolled_at']
    list_filter = ['payment_status']
    search_fields = ['student__email', 'course__title']


@admin.register(VideoProgress)
class VideoProgressAdmin(admin.ModelAdmin):
    list_display = ['student', 'lesson', 'watched_percent', 'completed']
    list_filter = ['completed']


@admin.register(ClassTiming)
class ClassTimingAdmin(admin.ModelAdmin):
    list_display = ['course', 'trainer', 'date', 'day_of_week', 'start_time', 'end_time']


@admin.register(PartnerCompany)
class PartnerCompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'min_score_required', 'is_active']
    list_editable = ['is_active']
    filter_horizontal = ['courses']