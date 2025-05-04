from django.shortcuts import render, get_object_or_404
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group

from pages.models import Course, Faculty

from .forms import CourseEnrollForm


class StudentHomePage(ListView):
    model = Course
    template_name = 'courses/student_home.html'
    context_object_name = 'courses'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = self.request.user.courses_joined.all()
        context['faculties'] = Faculty.objects.all()
        context['is_instructor'] = self.request.user.groups.filter(name="Instructors").exists()
        return context



class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/student_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty_slug = self.kwargs.get('faculty', None)

        # Get all courses joined by the student
        courses = Course.objects.filter(students=self.request.user)

        # Get all faculties related to the student's courses
        faculties = Faculty.objects.filter(faculty_courses__in=courses).distinct()

        # Filter courses by faculty if a faculty slug is provided
        if faculty_slug:
            faculty = get_object_or_404(Faculty, slug=faculty_slug)
            courses = courses.filter(faculty=faculty)
            context['faculty'] = faculty  # Pass the selected faculty to the template

        context['courses'] = courses
        context['faculties'] = faculties
        return context


