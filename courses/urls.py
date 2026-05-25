from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('course/<int:course_id>/', views.course_detail_view, name='course_detail'),
    # Add this line to your urlpatterns list:

    # Enroll + Payment
    path('enroll/<int:course_id>/', views.enroll_view, name='enroll'),
    path('payment/<int:enrollment_id>/', views.payment_view, name='payment'),
    path('payment/<int:enrollment_id>/confirm/', views.payment_confirm_view, name='payment_confirm'),
    path('payment/verify/', views.payment_verify_view, name='payment_verify'),

    # Course player & progress
    path('course/<int:course_id>/player/', views.course_player_view, name='course_player'),
    path('lesson/<int:lesson_id>/progress/', views.update_progress_view, name='update_progress'),
    path('my-courses/', views.my_courses_view, name='my_courses'),

    # Trainer
    path('trainer/course/<int:course_id>/lessons/', views.upload_lesson_view, name='upload_lesson'),
    path('trainer/lesson/<int:lesson_id>/delete/', views.delete_lesson_view, name='delete_lesson'),
    path('trainer/course/<int:course_id>/timings/', views.class_timings_view, name='class_timings'),
    path('trainer/course/<int:course_id>/timing/<int:timing_id>/attendance/', views.class_attendance_view, name='class_attendance'),

    # Category pages
    path('courses/accounting/', views.category_view, {'category': 'accounting'}, name='Accounting'),
    path('courses/business/',   views.category_view, {'category': 'business'},   name='Business'),
    path('courses/diet/',       views.category_view, {'category': 'diet'},       name='diet'),
    path('courses/computer-science/', views.category_view, {'category': 'computer_science'}, name='computer_science'),
    # testinomial
    
]