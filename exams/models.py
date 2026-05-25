from django.db import models
from django.conf import settings
from courses.models import Course


class Question(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    option_a = models.CharField(max_length=300)
    option_b = models.CharField(max_length=300)
    option_c = models.CharField(max_length=300)
    option_d = models.CharField(max_length=300)
    correct_option = models.CharField(max_length=1, choices=[
        ('a', 'A'), ('b', 'B'), ('c', 'C'), ('d', 'D')
    ])
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def get_options(self):
        return {
            'a': self.option_a,
            'b': self.option_b,
            'c': self.option_c,
            'd': self.option_d,
        }

    def __str__(self):
        return f"[{self.course.title}] {self.text[:60]}"


class ExamAttempt(models.Model):
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='exam_attempts'
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exam_attempts')
    score = models.PositiveIntegerField(default=0)
    total_questions = models.PositiveIntegerField(default=0)
    percentage = models.FloatField(default=0.0)
    passed = models.BooleanField(default=False)          # >= 50%
    eligible_for_partner = models.BooleanField(default=False)  # >= 70%
    attempted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.email} — {self.course.title} ({self.percentage:.1f}%)"


class ExamAnswer(models.Model):
    attempt = models.ForeignKey(ExamAttempt, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    selected_option = models.CharField(max_length=1)
    is_correct = models.BooleanField(default=False)