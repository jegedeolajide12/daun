from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import CourseEnrollForm
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group

from pages.models import Course, Faculty

class StudentHomePage(ListView):
    model = Course
    template_name = 'courses/student_home.html'
    context_object_name = 'courses'
    def get_context_data(self, **kwargs):
        instructor_group = Group.objects.get(name="Instructors").user_set.all()
        context = super().get_context_data(**kwargs)
        context['courses'] = Course.objects.all()
        context['faculties'] = Faculty.objects.all()
        context['is_instructor'] = self.request.user.groups.filter(name="Instructors").exists()
        return context



class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/course/student_courses.html'

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])