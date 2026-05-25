from django.urls import path
from . import api_views

urlpatterns = [
    path('courses/', api_views.CourseListAPIView.as_view(), name='api_courses'),
    path('courses/<int:pk>/', api_views.CourseDetailAPIView.as_view(), name='api_course_detail'),
    path('courses/with_progress/', api_views.CoursesWithProgressAPIView.as_view(), name='api_courses_progress'),
    path('lesson/<int:lesson_id>/progress/', api_views.UpdateProgressAPIView.as_view(), name='api_update_progress'),
]