from django.urls import path
from .views import StudentRegistrationView

app_name = 'student'

urlpatterns = [
    path('register/', StudentRegistrationView.as_view(), name='student_registration'),
]