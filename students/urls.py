from django.urls import path
from .views import StudentEnrollCourseView, StudentHomePage, StudentCourseListView

app_name = 'student'

urlpatterns = [
    path('student/home/', StudentHomePage.as_view(), name='student_home'),
    path('enroll-course/', StudentEnrollCourseView.as_view(), name='student_enroll_course'),
]