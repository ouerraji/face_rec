import base64
import datetime

import cv2
import face_recognition
import numpy as np
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.files.base import ContentFile
from django.shortcuts import render

# Create your views here.
from django.shortcuts import render,redirect
from django.contrib import messages
from django.utils import timezone

from face_rec1.models import Student, Attendance
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login

def index(request):
    return render(request, 'face_rec1/index.html')


def student_registration(request):
    if request.method == 'POST':
        try:
            # Get form data
            name = request.POST.get('name')
            email = request.POST.get('email')
            phone = request.POST.get('phone')
            class_name = request.POST.get('class')
            speciality = request.POST.get('speciality')
            image_data = request.POST.get('image')

            # Process the base64 image
            if image_data:
                # Remove the data:image/jpeg;base64, prefix if present
                if 'base64,' in image_data:
                    image_data = image_data.split('base64,')[1]

                # Convert base64 to image file
                image_content = ContentFile(base64.b64decode(image_data))

                # Create student instance
                student = Student(
                    name=name,
                    email=email,
                    phone=phone,
                    class_name=class_name,
                    speciality=speciality,
                )

                # Save the image
                student.photo.save(f"{name}.jpg", image_content, save=False)
                student.save()

                return redirect('face_rec1:index')
            else:
                error_message = "Photo is required"
                return render(request, 'face_rec1/student_registration.html',
                              {'error_message': error_message})

        except Exception as e:
            error_message = str(e)
            return render(request, 'face_rec1/student_registration.html',
                          {'error_message': error_message})

    return render(request, 'face_rec1/student_registration.html')


def teacher_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None and user.is_staff:
            login(request, user)
            return redirect('face_rec1:student_list')
        else:
            messages.error(request, 'Invalid credentials or insufficient permissions.')

    return render(request, 'face_rec1/teacher_login.html')

@login_required(login_url='face_rec1:teacher_login')
def student_list(request):
    # Get unauthorized students only
    students = Student.objects.filter(authorized=False)
    return render(request, 'face_rec1/student_list.html', {'students': students})

@login_required(login_url='face_rec1:teacher_login')
def authorize_student(request, student_id):
    if request.method == 'POST':
        try:
            student = Student.objects.get(id=student_id)
            # Toggle the authorized status
            student.authorized = not student.authorized
            student.save()

            action = "authorized" if student.authorized else "revoked authorization for"
            messages.success(request, f'Successfully {action} {student.name}')
        except Student.DoesNotExist:
            messages.error(request, 'Student not found.')

    return redirect('face_rec1:student_list')


def attendance_details(request):
    # Get the search date from the request, default to today
    search_date = request.GET.get('search_date')

    # Base queryset
    attendances = Attendance.objects.select_related('student').order_by('-time_in')

    # Filter by date if search_date is provided
    if search_date:
        attendances = attendances.filter(date=search_date)
    else:
        # Default to today's records
        today = timezone.now().date()
        attendances = attendances.filter(date=today)

    context = {
        'attendances': attendances,
        'search_date': search_date if search_date else timezone.now().date().strftime('%Y-%m-%d'),
    }

    return render(request, 'face_rec1/attendance_details.html', context)


def mark_attendance(request):
    try:
        # Initialize video capture
        video_capture = cv2.VideoCapture(0)

        # Load authorized students' face encodings
        authorized_students = Student.objects.filter(authorized=True)
        print("Found authorized students:", authorized_students)
        known_face_encodings = []
        known_face_names = []

        for student in authorized_students:
            try:
                print(f"Processing student photo: {student.photo.path}")
                image = face_recognition.load_image_file(student.photo.path)
                rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

                print("Getting face encodings...")
                encodings = face_recognition.face_encodings(rgb_image)

                if len(encodings) > 0:
                    face_encoding = encodings[0]
                    known_face_encodings.append(face_encoding)
                    known_face_names.append(student.name)
                    print(f"Successfully encoded face for {student.name}")
                else:
                    print(f"No face found in image for {student.name}")

            except Exception as e:
                print(f"Error processing {student.name}'s image: {str(e)}")
                import traceback
                traceback.print_exc()
                continue

        print(f"Successfully loaded {len(known_face_encodings)} face encodings")

        # Initialize variables
        process_this_frame = True
        current_face_locations = []
        current_face_names = []

        # Keep track of recognized students to avoid duplicate records
        recognized_students = set()

        while True:
            ret, frame = video_capture.read()

            if process_this_frame:
                small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
                rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

                face_locations = face_recognition.face_locations(rgb_small_frame)
                face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

                face_names = []
                for face_encoding in face_encodings:
                    matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
                    name = "Unknown"

                    if True in matches:
                        face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                        best_match_index = np.argmin(face_distances)
                        if matches[best_match_index]:
                            name = known_face_names[best_match_index]

                            # Only process attendance if we haven't seen this student yet
                            if name not in recognized_students:
                                try:
                                    student = authorized_students.get(name=name)
                                    now = timezone.now()
                                    today = now.date()
                                    current_time = now.time()

                                    # Check if attendance record exists for today
                                    attendance, created = Attendance.objects.get_or_create(
                                        student=student,
                                        date=today,
                                        defaults={
                                            'time_in': current_time,
                                            'status': 'Present'
                                        }
                                    )

                                    if created:
                                        # If created after a certain time (e.g., 9 AM), mark as late
                                        late_threshold = datetime.time(16, 0)  # 9 AM
                                        if current_time > late_threshold:
                                            attendance.status = 'Late'
                                            attendance.save()

                                        print(f"Marked {name} as {attendance.status} at {current_time}")
                                    else:
                                        print(f"{name} already marked for today at {attendance.time_in}")

                                    # Add to recognized set to avoid duplicate processing
                                    recognized_students.add(name)

                                except Exception as e:
                                    print(f"Error marking attendance for {name}: {str(e)}")
                                    import traceback
                                    traceback.print_exc()

                    face_names.append(name)

                current_face_locations = face_locations
                current_face_names = face_names

            process_this_frame = not process_this_frame

            # Display results (rest of the display code remains the same)
            for (top, right, bottom, left), name in zip(current_face_locations, current_face_names):
                # Scale back up face locations
                top *= 4
                right *= 4
                bottom *= 4
                left *= 4

                # Draw box
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)

                # Calculate label dimensions
                label_height = 35
                label_width = right - left
                cv2.rectangle(frame, (left, bottom - label_height), (right, bottom), (0, 0, 255), cv2.FILLED)

                # Add text
                font = cv2.FONT_HERSHEY_DUPLEX
                cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.6, (255, 255, 255), 1)

            cv2.imshow('Video', frame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

        video_capture.release()
        cv2.destroyAllWindows()

        return render(request, 'face_rec1/mark_attendance.html')

    except Exception as e:
        print(f"Error in mark_attendance: {str(e)}")
        import traceback
        traceback.print_exc()
        return render(request, 'face_rec1/mark_attendance.html', {'error': str(e)})

