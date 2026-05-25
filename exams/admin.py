from django.contrib import admin
from .models import Question, ExamAttempt, ExamAnswer


class ExamAnswerInline(admin.TabularInline):
    model = ExamAnswer
    extra = 0
    readonly_fields = ['question', 'selected_option', 'is_correct']


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'course', 'correct_option', 'order']
    list_filter = ['course']
    search_fields = ['text', 'course__title']
    ordering = ['course', 'order']


@admin.register(ExamAttempt)
class ExamAttemptAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'score', 'total_questions', 'percentage', 'passed', 'attempted_at']
    list_filter = ['passed', 'eligible_for_partner']
    search_fields = ['student__email', 'course__title']
    readonly_fields = ['percentage', 'passed', 'eligible_for_partner']
    inlines = [ExamAnswerInline]