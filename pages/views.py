from django.shortcuts import render, get_object_or_404, redirect
from django.utils.timezone import now
from django.urls import reverse 
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView,UpdateView,DeleteView
from django.views.generic.base import TemplateResponseMixin, View
from django.db.models import Count
from django.contrib import messages
from django.utils.text import slugify
from django.db import IntegrityError
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.forms.models import modelform_factory
from django.apps import apps
from django.contrib.auth.models import Group
from django.http import JsonResponse

from actstream import action
from students.forms import CourseEnrollForm

from .models import Course, Content, Topic, Video, Faculty, Notification, Enrollment, Assignment,Submission
from .forms import CourseForm, ModuleFormSet, FacultyForm, AssignmentForm, SubmissionForm

def create_faculty(request):
    if request.method == "POST":
        form = FacultyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Faculty created successfully!")
    return redirect('account:dashboard')
    

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
            enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)  # Create an enrollment record
            if created:
                course.students.add(request.user)  # Enroll the user in the course
                # Optionally, you can also create a notification for the course owner
                Notification.objects.create(
                    sender = request.user,
                    related_course=course,
                    recipient=course.owner,
                    related_enrollment=enrollment,

                    title="Enrollment Notification",
                    message=f"{request.user.username} has enrolled in your course: {course.name}",
                    notification_type="Enrollment",
                    is_read=False
                )
                action.send(request.user, verb='Enrolled in', target=course)
                messages.success(request, "You have successfully enrolled in the course!")
                return redirect('course:course', course_slug=course.slug)
            else:
                messages.error(request, "You are already enrolled in this course.")
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
        Enrollment.objects.filter(student=request.user, course=course).delete()
        # Optionally, you can also delete the enrollment record
        # action.send(request.user, verb='Unenrolled from', target=course)
        # Create a notification for the user
        Notification.objects.create(
            sender = request.user,
            related_course=course,
            recipient=course.owner,
            
            title="Unenrollment Notification",
            message=f"You have been unenrolled from the course: {course.name}",
            notification_type="Unenrollment",
            is_read=False
        )
        # Send a notification to the user

        action.send(request.user, verb='Unenrolled from', target=course)
        messages.success(request, "You have successfully unenrolled from the course!")
        return redirect('course:course', course_slug=course.slug)

    context = {'course': course}
    return render(request, 'courses/manage/course/course_detail.html', context)

def topic_detail(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    contents = Content.objects.prefetch_related('content_type').filter(topic=topic)
    assignments = topic.course.assignments.all()

    # Get the ContentType for the Video model
    video_content_type = ContentType.objects.get_for_model(Video)

    # Filter by the ContentType instance
    video_count = contents.filter(content_type=video_content_type).count()


    context = {'topic': topic, 'contents': contents, 'video_count': video_count, 'assignments': assignments, 'now': now}
    return render(request, 'courses/manage/module/module_detail.html', context)


class CourseListView(TemplateResponseMixin, View):
    model = Course
    template_name = 'courses/course_list.html'
    
    def get(self, request, *args, **kwargs):
        faculties = Faculty.objects.all()
        courses = Course.objects.all()
        is_instructor = self.request.user.groups.filter(name='Instructors').exists()
        return self.render_to_response({'faculties':faculties, 'courses':courses,'is_instructor':is_instructor})

@require_POST
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(
        Notification, 
        id=notification_id, 
        recipient=request.user
    )
    notification.mark_as_read()
    return JsonResponse({'status': 'success'})

@require_POST
def mark_all_notifications_read(request):
    notifications = request.user.notifications.filter(is_read=False)
    for notification in notifications:
        notification.mark_as_read()
    return JsonResponse({'status': 'success'})

@login_required
def get_notifications(request):
    notifications = request.user.notifications.filter(is_read=False).order_by('-created_at')[:10]
    data = [{
        'id': n.id,
        'title': n.title,
        'message': n.message,
        'type': n.notification_type,
        'timestamp': n.created_at.strftime('%b %d, %H:%M'),
        'course': n.related_course.name if n.related_course else None,
        'url': reverse('course:course', args=[n.related_course.id]) if n.related_course else '#'
    } for n in notifications]
    return JsonResponse(data, safe=False)

@login_required
def create_assignment(request):
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, user=request.user)
        course_id = request.POST.get('course')
        if course_id:
            form.fields['topic'].queryset = Topic.objects.filter(course_id=course_id)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.is_graded = False
            assignment.save()
            messages.success(request, "Assignment created successfully!")
            # Optionally, you can also create a notification for the course owner
            Notification.objects.create(
                related_course = assignment.course,
                recipient=request.user,
                title = "Assignment Notification",
                message=f"You have created a new assignment: {assignment.title}",
                notification_type="Assignment",
                is_read=False
            )
            for recipient in assignment.course.students.all():
                Notification.objects.create(
                    sender=request.user,
                    related_course=assignment.course,
                    recipient=recipient,
                    related_enrollment=assignment.course.enrollments.filter(student=recipient).first(),
                    title="Assignment Notification",
                    message=f"You have a new Assignment: {assignment.title}",
                    notification_type="Assignment",
                    is_read=False
                )
            return redirect('account:dashboard')
        else:
            form = AssignmentForm(request.POST, user=request.user)
            messages.error(request, "There was an error creating the assignment. Please correct the errors below.")
    else:
        form = AssignmentForm()
    # Get the list of courses for the dropdown
    courses = Course.objects.filter(owner=request.user)
    return render(request, 'students/manage/create_assignment.html', {'form': form, 'courses': courses})


@login_required
def submit_assignment(request, course_id, topic_id, assignment_id):
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(Topic, id=topic_id, course=course)
    assignment = get_object_or_404(Assignment, id=assignment_id, topic=topic)
    
    if not course.students.filter(id=request.user.id).exists():
        messages.error(request, "You are not enrolled in this course.")
        return redirect('course:topic_detail', topic_id=topic.id)
    
    if assignment.is_graded:
        messages.error(request, "Submissions for this assignment are graded and closed for you.")
        return redirect('course:topic_detail', topic_id=topic.id)
    
    
    
    existing_submission = Submission.objects.filter(assignment=assignment).first()
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES, instance=existing_submission)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.user = request.user
            submission.assignment = assignment
            assignment.status = 'submitted'
            assignment.save()  # Save the updated status to the database
            submission.save()
            
            # Handle file uploads
            for file in request.FILES.getlist('files'):
                submission.files.create(file=file)
            
            # Create notification for student
            Notification.objects.create(
                recipient=request.user,
                notification_type='Submission',
                title=f"Assignment submission: {assignment.title}",
                message=f"You have successfully submitted {assignment.title}",
                related_course=course,
                is_read=False
            )
            
            # Create notification for instructor
            Notification.objects.create(
                sender=request.user,
                recipient=course.owner,
                notification_type='Submission',
                title=f"New submission in {course.name}",
                message=f"{request.user.get_full_name()} submitted {assignment.title}",
                related_course=course,
                is_read=False
            )
            
            messages.success(request, "Your assignment has been submitted successfully!")
            return redirect('course:topic_detail', topic_id=topic.id)
        else:
            form = SubmissionForm(request.POST, request.FILES)
            messages.error(request, "There was an error while submitting your asssignment. Correct the errors below")
    else:
        form = SubmissionForm()
    
    context = {
        'course': course,
        'topic': topic,
        'assignment': assignment,
        'form': form
    }
    return render(request, 'students/manage/submit_asignment.html', context)


def load_topics(request):
    course_id = request.GET.get('course_id')
    topics = Topic.objects.filter(course_id=course_id).order_by('order')
    
    # Return both id and the formatted string (including order number)
    data = [{
        'id': topic.id,
        'name': str(topic)  # This uses your __str__ method
    } for topic in topics]
    
    return JsonResponse(data, safe=False)