from django.urls import path
from . import api_views

urlpatterns = [
    path('exam/submit/', api_views.ExamSubmitAPIView.as_view(), name='api_exam_submit'),
    path('exam/results/', api_views.ExamResultsAPIView.as_view(), name='api_exam_results'),
    path('exam/result/<int:attempt_id>/', api_views.ExamResultDetailAPIView.as_view(), name='api_exam_result_detail'),
    path('exams/questions/<int:course_id>/', api_views.ExamQuestionsAPIView.as_view(), name='api_exam_questions'),
    path('exams/progress/', api_views.ExamProgressAPIView.as_view(), name='api_exam_progress'),
]