from django.urls import path
from .views import StudentHomePage, StudentCourseListView

app_name = 'student'

urlpatterns = [
    path('student/home/', StudentHomePage.as_view(), name='student_home'),
]