from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('trainer', 'Trainer'),
        ('admin', 'Admin'),
    ]
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"

    def get_dashboard_url(self):
        urls = {
            'student': '/dashboard/student/',
            'trainer': '/dashboard/trainer/',
            'admin':   '/dashboard/admin/',
        }
        return urls.get(self.role, '/')


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        from django.utils import timezone
        from datetime import timedelta
        return (
            not self.is_used and
            self.created_at >= timezone.now() - timedelta(minutes=10)
        )


class Testimonial(models.Model):
    student = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE,
        related_name='testimonials',
        limit_choices_to={'role': 'student'}
    )
    message = models.TextField(max_length=500)
    rating = models.PositiveIntegerField(default=5)   # 1–5
    is_approved = models.BooleanField(default=False)  # admin approves before showing
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.student.get_full_name()} — {self.rating}★"