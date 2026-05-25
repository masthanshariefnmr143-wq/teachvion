from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('register/success/', views.register_success_view, name='register_success'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('verify-otp/', views.verify_otp_view, name='verify_otp'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
    path('profile/', views.profile_view, name='profile'),
    path('testinomial/submit/',views.submit_testimonial_view,name="submit_testinomial"),
    
]