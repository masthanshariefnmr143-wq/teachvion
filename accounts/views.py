import random
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from .models import CustomUser, PasswordResetOTP
from .forms import (
    RegisterForm, LoginForm, ForgotPasswordForm,
    OTPVerifyForm, ResetPasswordForm, ProfileUpdateForm
)
def index(request):
    return render(request,'index.html')

# ─── Register ────────────────────────────────────────────────────
def register_view(request):
    form = RegisterForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Account created! Welcome, {user.first_name}.")
            return redirect('register_success')
        else:
            messages.error(request, "Please fix the errors below.")
    return render(request, 'register.html', {'form': form})


def register_success_view(request):
    return render(request, 'register_success.html')


# ─── Login ───────────────────────────────────────────────────────
def login_view(request):
    if request.user.is_authenticated:
        return redirect(request.user.get_dashboard_url())

    form = LoginForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email'].lower()
            password = form.cleaned_data['password']
            user = authenticate(request, username=email, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next', user.get_dashboard_url())
                return redirect(next_url)
            else:
                messages.error(request, "Invalid email or password.")
    return render(request, 'login.html', {'form': form})


# ─── Logout ──────────────────────────────────────────────────────
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "Logged out successfully.")
    return redirect('login')


# ─── Forgot Password (step 1: enter email) ───────────────────────
def forgot_password_view(request):
    form = ForgotPasswordForm(request.POST or None)
    if request.method == 'POST':
        if form.is_valid():
            email = form.cleaned_data['email']
            user = CustomUser.objects.get(email=email)

            # Generate 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            PasswordResetOTP.objects.create(user=user, otp=otp_code)

            # Send email
            send_mail(
                subject='Teachvion — Password Reset OTP',
                message=f'Your OTP to reset password is: {otp_code}\nThis OTP expires in 10 minutes.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                fail_silently=False,
            )
            messages.success(request, "OTP sent to your email.")
            return redirect(f'/verify-otp/?email={email}')
    return render(request, 'forgot_password.html', {'form': form})


# ─── Verify OTP (step 2) ─────────────────────────────────────────
def verify_otp_view(request):
    email = request.GET.get('email', '') or request.POST.get('email', '')
    form = OTPVerifyForm(request.POST or None, initial={'email': email})

    if request.method == 'POST':
        if form.is_valid():
            entered_otp = form.cleaned_data['otp']
            try:
                user = CustomUser.objects.get(email=email)
                otp_obj = PasswordResetOTP.objects.filter(
                    user=user, otp=entered_otp, is_used=False
                ).latest('created_at')
                if otp_obj.is_valid():
                    return redirect(f'/reset-password/?email={email}&otp={entered_otp}')
                else:
                    messages.error(request, "OTP has expired. Please request a new one.")
            except (CustomUser.DoesNotExist, PasswordResetOTP.DoesNotExist):
                messages.error(request, "Invalid OTP.")
    return render(request, 'verify_otp.html', {'form': form, 'email': email})


# ─── Reset Password (step 3) ─────────────────────────────────────
def reset_password_view(request):
    email = request.GET.get('email', '') or request.POST.get('email', '')
    otp = request.GET.get('otp', '') or request.POST.get('otp', '')
    form = ResetPasswordForm(request.POST or None, initial={'email': email, 'otp': otp})

    if request.method == 'POST':
        if form.is_valid():
            try:
                user = CustomUser.objects.get(email=email)
                otp_obj = PasswordResetOTP.objects.filter(
                    user=user, otp=otp, is_used=False
                ).latest('created_at')
                if otp_obj.is_valid():
                    user.set_password(form.cleaned_data['password1'])
                    user.save()
                    otp_obj.is_used = True
                    otp_obj.save()
                    messages.success(request, "Password reset successfully. Please login.")
                    return redirect('login')
                else:
                    messages.error(request, "OTP expired.")
            except (CustomUser.DoesNotExist, PasswordResetOTP.DoesNotExist):
                messages.error(request, "Invalid request.")
    return render(request, 'reset_password.html', {'form': form})


# ─── Profile ─────────────────────────────────────────────────────
@login_required
def profile_view(request):
    form = ProfileUpdateForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect('profile')
    return render(request, 'profile.html', {'form': form})

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
from .models import Testimonial


# ------ Submit Testimonial ------
@login_required
def submit_testimonial_view(request):
    if request.user.role != "student":
        return JsonResponse(
            {
                "status": "error",
                "message": "Only students can submit testimonials.",
            }
        )

    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        rating = int(request.POST.get("rating", 5))

        if message and 1 <= rating <= 5:
            Testimonial.objects.create(
                student=request.user,
                message=message,
                rating=rating,
                is_approved=False,
            )
            messages.success(
                request,
                "Thank you! Your testimonial has been submitted for review.",
            )
        else:
            messages.error(
                request, "Please write a message and select a rating."
            )
        return redirect("student_dashboard")

    return redirect("student_dashboard")