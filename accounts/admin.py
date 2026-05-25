from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, PasswordResetOTP,Testimonial


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_active', 'created_at']
    list_filter = ['role', 'is_active']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('Teachvion', {'fields': ('role', 'phone', 'bio', 'profile_pic')}),
    )


@admin.register(PasswordResetOTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'otp', 'created_at', 'is_used']


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display=['student','rating','is_approved','created_at']
    list_filter=['is_approved','rating']
    list_editable=['is_approved']
    search_fields=['student_email','message']
    actions=['approve_selected']

    def approve_selected(self,request,queryset):
        queryset.update(is_approved=True)
    approve_selected.short_description="Approve selected testinomials"

