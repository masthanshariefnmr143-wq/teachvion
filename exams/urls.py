from django.urls import path
from . import views

urlpatterns = [
    path('exam/', views.exam_hub_view, name='exam'),
    path('exam/<int:course_id>/', views.exam_view, name='take_exam'),
    path('exam/result/<int:attempt_id>/', views.exam_result_view, name='exam_result'),
]