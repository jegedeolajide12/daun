from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.views.generic.base import TemplateResponseMixin, View
from django.db.models import Count
from django.contrib import messages
from django.utils.text import slugify
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.forms.models import modelform_factory
from django.apps import apps
from django.contrib.auth.models import Group

from actstream import action
from students.forms import CourseEnrollForm

from .models import Course, Content, Topic, Video, Faculty
from .forms import CourseForm, ModuleFormSet, FacultyForm

def create_faculty(request):
    if request.method == "POST":
        form = FacultyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Faculty created successfully!")
    return redirect('course:home')
    

class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/formset.html'
    course = None

    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)
    
    def dispatch(self, request, course_slug):
        try:
            self.course = get_object_or_404(Course, slug=course_slug, owner = request.user)
        except Course.DoesNotExist:
            # Handle the case where the course does not exist
            messages.error(request, "You do not own this course")
            return redirect('course:home')
        return super().dispatch(request, course_slug)
    
    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({'course':self.course, 'formset':formset})
    
    def post(self, request, course_slug, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        self.course = get_object_or_404(Course, slug=course_slug, owner = request.user)
        if formset.is_valid():
            for form in formset:
                if form.cleaned_data and any(form.cleaned_data.values()):  # Skip empty forms
                    form.save()
            formset.save()
            return redirect('course:course', self.course.slug)
        else:
            print(formset.errors)
        return self.render_to_response({'course':self.course, 'formset':formset})

class ContentCreateUpdateView(TemplateResponseMixin, View):
    topic = None
    model = None
    obj = None
    context_object_name = 'topic'
    template_name = 'courses/manage/content/form.html'

    def get_model(self, model_name):
        if model_name in ['text','video','image','file']:
            return apps.get_model(app_label='pages', model_name=model_name)
        return None
    
    def get_form(self, model, *args, **kwargs):
        Form  = modelform_factory(model, exclude=['owner', 'order', 'created', 'updated'])
        return Form(*args, **kwargs)
    
    def dispatch(self, request, topic_id, model_name, id=None):
        self.topic = get_object_or_404(Topic, id=topic_id, course__owner=request.user)
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model, id=id, owner=request.user)
        return super().dispatch(request, topic_id, model_name, id)
    
    def get(self, request, topic_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form':form, 'objects':self.obj})
    
    def post(self, request, topic_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj, data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                Content.objects.create(topic=self.topic, item=obj)
            return redirect('course:topic_detail', self.topic.id)
        return self.render_to_response({'form':form, 'object':self.obj})

class ContentDeleteView(View):
    def post(self, request, content_id):
        content = get_object_or_404(Content, id=content_id, topic__course__owner=request.user)
        topic = content.topic
        if content.item.owner != request.user:
            return redirect('course:topic_detail', content.topic.id)  # Redirect if not the owner
        if content.item:
            content.item.delete()
        content.delete()
        return redirect('course:topic_detail', topic.id)
    

class OwnerMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)
    

class OwnerEditMixin:
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnerCourseMixin(OwnerMixin, LoginRequiredMixin, PermissionRequiredMixin):
    model = Course
    form_class = CourseForm
    success_url = reverse_lazy('course:home')


class OwnerCourseCreateMixin(OwnerCourseMixin, CreateView):
    template_name = 'courses/manage/course/create_course.html'
    permission_required = 'pages.add_course'

    
    def form_valid(self, form):
        form.instance.owner = self.request.user
        form.instance.slug = slugify(form.instance.name)
        try:
            return super().form_valid(form)
        except IntegrityError:
            messages.error(self.request, "A course with this name already exists. Please choose a different name.")
            form.add_error('name', "A course with this name already exists.")
            return self.form_invalid(form)  # This returns a response

        # ✅ Always end with a return, though this line will never be reached.
        return super().form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "There was an error with your submission. Please correct the errors below.")
        return super().form_invalid(form)


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = 'courses/manage/course/edit_course.html'

def index(request):
    courses = Course.objects.all()
    is_instructor = request.user.groups.filter(name='Instructors').exists()
    context = {'courses':courses,'is_instructor':is_instructor}
    return render(request, 'courses/index.html', context)

class ManageCourseListView(OwnerCourseMixin, ListView):
    context_object_name = 'courses'
    template_name = 'courses/manage/course/list.html'
    permission_required = 'pages.view_course'

    def get_queryset(self):
        courses = Course.objects.filter(owner=self.request.user)
        return courses
class CourseCreateView(OwnerCourseCreateMixin):
    permission_required = 'pages.add_course'



class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = 'pages.change_course'

class CourseDeleteView(OwnerCourseMixin, DeleteView):
    permission_required = 'pages.delete_course'
    template_name = 'courses/manage/course/delete_confirm.html'
    success_url = reverse_lazy('course:home')  # Redirect after successful deletion

    def post(self, request, *args, **kwargs):
        messages.success(request, "Course deleted successfully!")
        return super().post(request, *args, **kwargs)


@login_required
def course_detail(request, course_slug):
    course = get_object_or_404(Course.objects.annotate(total_topics=Count('course_topics')), slug__iexact=course_slug)
    owner = course.owner
    is_student = course.students.filter(id=request.user.id).exists()
    is_instructor = request.user.groups.filter(name="Instructors").exists()
    is_admin = request.user.groups.filter(name="Admin")

    if request.method == 'POST':
        # Handle form submission
        enroll_form = CourseEnrollForm(request.POST)
        if enroll_form.is_valid():
            course.students.add(request.user)  # Enroll the user in the course
            action.send(request.user, verb='Enrolled in', target=course)
            messages.success(request, "You have successfully enrolled in the course!")
            return redirect('course:course', course_slug=course.slug)
    else:
        # Initialize the enrollment form with the current course
        enroll_form = CourseEnrollForm(initial={'course': course})

    context = {'course': course, 'enroll_form': enroll_form, 'owner': owner, 'is_student': is_student, 'is_admin':is_admin, 'is_instructor': is_instructor}
    return render(request, 'courses/manage/course/course_detail.html', context)

def course_unenroll(request, course_slug):
    course = get_object_or_404(Course, slug=course_slug)
    if request.method == 'POST':
        course.students.remove(request.user)  # Unenroll the user from the course
        action.send(request.user, verb='Unenrolled from', target=course)
        messages.success(request, "You have successfully unenrolled from the course!")
        return redirect('course:course', course_slug=course.slug)

    context = {'course': course}
    return render(request, 'courses/manage/course/course_detail.html', context)

def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    contents = Content.objects.prefetch_related('content_type').filter(topic=topic)

    # Get the ContentType for the Video model
    video_content_type = ContentType.objects.get_for_model(Video)

    # Filter by the ContentType instance
    video_count = contents.filter(content_type=video_content_type).count()


    context = {'topic': topic, 'contents': contents, 'video_count': video_count}
    return render(request, 'courses/manage/module/module_detail.html', context)


class CourseListView(TemplateResponseMixin, View):
    model = Course
    template_name = 'courses/course_list.html'
    
    def get(self, request, *args, **kwargs):
        faculties = Faculty.objects.all()
        courses = Course.objects.all()
        is_instructor = self.request.user.groups.filter(name='Instructors').exists()
        return self.render_to_response({'faculties':faculties, 'courses':courses,'is_instructor':is_instructor})
