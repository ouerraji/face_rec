from django.urls import path
from . import views

app_name = 'face_rec1'

urlpatterns = [
    path('', views.index, name='index'),
path('capture_student/', views.student_registration, name='student_registration'),
    path('student-list/', views.student_list, name='student_list'),
path('teacher-login/', views.teacher_login, name='teacher_login'),
path('authorize-student/<int:student_id>/', views.authorize_student, name='authorize_student'),
    path('mark_attendance/', views.mark_attendance, name='mark_attendance'),
    path('attendance-details/', views.attendance_details, name='attendance_details'),
]