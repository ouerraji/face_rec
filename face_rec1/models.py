from django.db import models
from django.utils import timezone


# Create your models here.
class Student(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    class_name = models.CharField(max_length=50)
    speciality = models.CharField(max_length=2, choices=[
        ('GL', 'Génie Logiciel'),
        ('DS', 'Data Science'),
        ('RC', 'Réseau et Cloud'),
    ])
    photo = models.ImageField(upload_to='student_photos/')
    authorized = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.class_name} ({self.speciality})"

from django.db import models

class Attendance(models.Model):
    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendances',
        null=True  # Add this temporarily
    )
    date = models.DateField(default=timezone.now)  # Added default
    time_in = models.TimeField(default=timezone.now)  # Added default
    status = models.CharField(max_length=20, choices=[
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late')
    ], default='Present')

    class Meta:
        unique_together = ['student', 'date']

    def __str__(self):
        # Handle case where student might be None
        student_name = self.student.name if self.student else "No Student"
        return f"{student_name} - {self.date} - {self.status}"