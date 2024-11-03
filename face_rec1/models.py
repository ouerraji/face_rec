from django.db import models

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
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, default="Absent")
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.status}"
