from django.db import models
from django.conf import settings


class Course(models.Model):
    CATEGORY_CHOICES = [
        ('web', 'Web Development'),
        ('java', 'Java Full Stack'),
        ('python', 'Python Full Stack'),
        ('data', 'Data Analytics'),
        ('ai', 'AI/ML'),
        ('accounting', 'Accounting & Finance'),
        ('business', 'Business Management'),
        ('diet', 'Diet & Nutrition'),
        ('computer_science', 'Computer Science'),
    ]

    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='courses_taught',
        limit_choices_to={'role': 'trainer'}
    )
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    thumbnail = models.ImageField(upload_to='course_thumbnails/', blank=True, null=True)
    badge = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_total_lessons(self):
        return self.lessons.count()

    def get_enrolled_count(self):
        return self.enrollments.filter(payment_status='paid').count()


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    video_file = models.FileField(upload_to='videos/', blank=True, null=True)
    video_url = models.URLField(blank=True)   # YouTube / Vimeo embed
    pdf_file = models.FileField(upload_to='lesson_pdfs/', blank=True, null=True)
    notes = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)
    duration_mins = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.course.title} — {self.title}"


class Enrollment(models.Model):
    PAYMENT_STATUS = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('refunded', 'Refunded'),
    ]
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS, default='pending')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    razorpay_order_id = models.CharField(max_length=100, blank=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'course']

    def __str__(self):
        return f"{self.student.email} → {self.course.title}"


class VideoProgress(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='video_progress')
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='progress')
    watched_percent = models.PositiveIntegerField(default=0)
    completed = models.BooleanField(default=False)
    last_watched = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['student', 'lesson']

    def __str__(self):
        return f"{self.student.email} — {self.lesson.title} ({self.watched_percent}%)"


class ClassTiming(models.Model):
    DAY_CHOICES = [
        ('mon', 'Monday'), ('tue', 'Tuesday'), ('wed', 'Wednesday'),
        ('thu', 'Thursday'), ('fri', 'Friday'), ('sat', 'Saturday'), ('sun', 'Sunday'),
    ]
    trainer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name='class_timings', limit_choices_to={'role': 'trainer'}
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='class_timings')
    date = models.DateField(blank=True, null=True)
    day_of_week = models.CharField(max_length=3, choices=DAY_CHOICES, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    meeting_link = models.URLField(blank=True)
    notes = models.TextField(blank=True)

    def __str__(self):
        if self.date:
            return f"{self.course.title} — {self.date} {self.start_time}"
        return f"{self.course.title} — {self.get_day_of_week_display()} {self.start_time}"

    @property
    def display_date(self):
        if self.date:
            return self.date.strftime('%a, %d %b %Y')
        return self.get_day_of_week_display()

    @property
    def attendance_present_count(self):
        return self.attendances.filter(attended=True).count()


class Attendance(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    class_timing = models.ForeignKey(
        ClassTiming,
        on_delete=models.CASCADE,
        related_name='attendances'
    )
    attendance_percent = models.PositiveSmallIntegerField(default=0)
    attended = models.BooleanField(default=True)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['student', 'class_timing']

    def __str__(self):
        return f"{self.student.email} — {self.class_timing.course.title} @ {self.class_timing.get_day_of_week_display()}"
    

class PartnerCompany(models.Model):
    name = models.CharField(max_length=200)
    # The error (E019) says 'courses' is missing
    courses = models.ManyToManyField('Course', related_name='partners', blank=True)
    # The error (E108) says 'min_score_required' is missing
    min_score_required = models.PositiveIntegerField(default=60)
    # The error (E108/E121) says 'is_active' is missing
    is_active = models.BooleanField(default=True)
    logo = models.ImageField(upload_to='partners/', blank=True, null=True)
    website = models.URLField(blank=True)

    def __str__(self):
        return self.name

# testinomials
