from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['certificate_number', 'student', 'course', 'delivery_method', 'issued_at']
    list_filter = ['delivery_method']
    search_fields = ['certificate_number', 'student__email', 'course__title']
    readonly_fields = ['certificate_number', 'issued_at']