from django.contrib import admin
# Register your models here.

from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name','photo', 'email', 'class_name', 'speciality', 'authorized')
    list_filter = ('authorized', 'speciality', 'class_name')
    search_fields = ('name', 'email')