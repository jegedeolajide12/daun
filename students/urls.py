from django.urls import path
from .views import StudentHomePage, StudentCourseListView

app_name = 'student'

urlpatterns = [
    path('student/home/', StudentHomePage.as_view(), name='student_home'),
    path('courses/<slug:faculty>/', StudentCourseListView.as_view(), name='student_courses_by_faculty'),
]