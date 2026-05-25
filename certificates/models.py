import uuid
from django.db import models
from django.conf import settings
from courses.models import Course


class Certificate(models.Model):
    DELIVERY_CHOICES = [
        ('digital', 'Digital Download'),
        ('post', 'Postal Mail'),
        ('pdf', 'PDF Download'),
    ]

    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    exam_attempt = models.OneToOneField(
        'exams.ExamAttempt', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='certificate'
    )
    certificate_number = models.CharField(max_length=20, unique=True, editable=False)
    delivery_method = models.CharField(max_length=10, choices=DELIVERY_CHOICES, default='digital')
    postal_address = models.TextField(blank=True)
    issued_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.certificate_number:
            self.certificate_number = f"TV-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.certificate_number} — {self.student.get_full_name()} — {self.course.title}"


class PartnerCompany(models.Model):
    name = models.CharField(max_length=200)
    logo = models.ImageField(upload_to='partners/', blank=True, null=True)
    description = models.TextField(blank=True)
    job_link = models.URLField()
    min_score_required = models.PositiveIntegerField(default=70)
    courses = models.ManyToManyField(Course, related_name='partner_companies', blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Partner Companies"