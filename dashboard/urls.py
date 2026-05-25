from django.urls import path
from . import views

urlpatterns = [
    # Dashboards
    path('dashboard/student/', views.student_dashboard_view, name='student_dashboard'),
    path('dashboard/trainer/', views.trainer_dashboard_view, name='trainer_dashboard'),
    path('dashboard/admin/', views.admin_dashboard_view, name='admin_dashboard'),

    # Admin CRUD
    path('admin-panel/student/<int:user_id>/edit/', views.admin_student_edit_view, name='admin_student_edit'),
    path('admin-panel/user/<int:user_id>/delete/', views.admin_user_delete_view, name='admin_user_delete'),
    path('admin-panel/course/create/', views.admin_course_create_view, name='admin_course_create'),
    path('admin-panel/course/<int:course_id>/edit/', views.admin_course_edit_view, name='admin_course_edit'),
    path('admin-panel/course/<int:course_id>/delete/', views.admin_course_delete_view, name='admin_course_delete'),
    path('admin-panel/course/<int:course_id>/assign-trainer/', views.admin_assign_trainer_view, name='admin_assign_trainer'),

]