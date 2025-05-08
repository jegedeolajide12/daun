from django.urls import path
from .views import StudentHomePage, StudentCourseListView, manage_students, student_detail, bulk_student_actions

app_name = 'student'

urlpatterns = [
    path('student/home/', StudentHomePage.as_view(), name='student_home'),
    path('courses/<slug:faculty>/', StudentCourseListView.as_view(), name='student_courses_by_faculty'),
    path('manage_students/', manage_students, name='manage_students'),
    path('student/<int:student_id>/', student_detail, name='student_detail'),
    path('bulk_student_actions/', bulk_student_actions, name='bulk_student_actions'),
]