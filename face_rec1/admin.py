from django.contrib import admin
# Register your models here.

from .models import Student, Attendance


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('name','photo', 'email', 'class_name', 'speciality', 'authorized')
    list_filter = ('authorized', 'speciality', 'class_name')
    search_fields = ('name', 'email')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'time_in', 'status')
    list_filter = ('status', 'date')
    search_fields = ('student__name',)  # This allows searching by student name
    date_hierarchy = 'date'  # Adds date-based navigation