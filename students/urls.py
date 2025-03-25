from django.urls import path
from .views import StudentRegistrationView, StudentEnrollCourseView

app_name = 'student'

urlpatterns = [
    path('register/', StudentRegistrationView.as_view(), name='student_registration'),
    path('enroll-course/', StudentEnrollCourseView.as_view(), name='student_enroll_course'),
]