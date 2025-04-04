from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.views.generic.base import TemplateResponseMixin, View
from django.db.models import Count
from django.contrib import messages

from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.forms.models import modelform_factory
from django.apps import apps

from students.forms import CourseEnrollForm

from .models import Course, Content, Topic, Video, Faculty
from .forms import CourseForm, ModuleFormSet


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


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = 'courses/manage/course/edit_course.html'

def index(request):
    courses = Course.objects.all()
    context = {'courses':courses}
    return render(request, 'courses/index.html', context)

class ManageCourseListView(OwnerCourseMixin, ListView):
    context_object_name = 'courses'
    template_name = 'courses/manage/course/list.html'
    permission_required = 'pages.view_course'

    def get_queryset(self):
        courses = Course.objects.filter(owner=self.request.user)

class CourseCreateView(OwnerCourseEditMixin, CreateView):
    permission_required = 'pages.add_course'

class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = 'pages.change_course'

class CourseDeleteView(OwnerCourseMixin, DeleteView):
    permission_required = 'pages.delete_course'
    template_name = 'courses/manage/course/delete_confirm.html'


@login_required
def course_detail(request, course_slug):
    course = get_object_or_404(Course.objects.annotate(total_topics=Count('course_topics')), slug__iexact=course_slug)
    # Initialize the enrollment form with the current course
    enroll_form = CourseEnrollForm(initial={'course': course})
    owner = course.owner
    context = {'course':course, 'enroll_form':enroll_form, 'owner':owner}
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
    template_name = 'courses/course/course_list.html'
    
    def get(self, request, faculty=None):
        faculties = Faculty.objects.annotate(total_courses=Count('faculty_courses'))
        courses = Course.objects.annotate(total_topics=Count('course_topics'))
        if faculty:
            faculty = get_object_or_404(Faculty, slug=faculty)
            courses = courses.filter(faculty=faculty)
        return self.render_to_response({'faculties':faculties, 'faculty':faculty, 'courses':courses})