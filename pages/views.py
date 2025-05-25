from django.shortcuts import get_object_or_404, redirect
from django.db import transaction
from django.shortcuts import render
from encodings.punycode import T
from multiprocessing import process
from os import name
from django import template
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
from django.core.paginator import Paginator
from django.forms import modelformset_factory

from django.core.files.storage import FileSystemStorage

from actstream import action
from requests import options
from daun.settings import TEMPLATES
from students.forms import CourseEnrollForm
from formtools.wizard.views import SessionWizardView

from .models import (
                Course, Content, Topic, Video, 
                Faculty, Notification, Enrollment, Assignment,
                Submission, UserTask, Grade, RubricScore, Rubric,
                MCQOption, Assessment, SubmissionFile, AssessmentQuestion,
                AssessmentAttempt, MCQResponse, CourseObjectives, CourseRequirements
                )
from .forms import (FacultyForm, CourseTopicAssignmentsForm, SubmissionForm, 
                    CourseTopicAssessmentsForm, MCQOptionForm, CourseBasicsForm, CourseTopicsForm,
                    CourseTopicContentsForm, AssessmentQuestionForm, CourseTrailerForm, CourseRequirementsForm, 
                    CourseMarketingForm, CourseObjectivesForm, CourseForm, ModuleFormSet)

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

ModuleFormSet = modelformset_factory(
    Topic,
    form=CourseTopicsForm,
    extra=1,
    can_delete=True
)
FORMS = [
    ('basics', CourseBasicsForm),
    ('topics', CourseTopicsForm),
    ('contents', CourseTopicContentsForm),
    ('assignments', CourseTopicAssignmentsForm),
    ('assessments', CourseTopicAssessmentsForm),
    ('marketing', CourseMarketingForm)
]

TEMPLATES = {
    'basics': 'courses/manage/course/create/course_basics.html',
    'topics': 'courses/manage/course/create/course_topics.html',
    'contents': 'courses/manage/course/create/course_contents.html',
    'assignments': 'courses/manage/course/create/course_assignments.html',
    'assessments': 'courses/manage/course/create/course_assessments.html',
    'marketing': 'courses/manage/course/create/course_marketing.html',
}
            
class CourseCreateWizard(SessionWizardView):
    template_name = 'courses/manage/course/create/course_basics.html'
    form_list = FORMS
    file_storage = FileSystemStorage(location='media/course_files')

    def get_template_names(self):
        step = self.steps.current
        return [TEMPLATES[step]]

    def process_step(self, form):
        step = self.steps.current
        course_id = self.storage.extra_data.get('course_id')
        course = Course.objects.get(id=course_id) if course_id else None

        if step == 'basics':
            data = form.cleaned_data
            files = self.request.FILES
            form.fields['faculty'].queryset = Faculty.objects.all()
            if data and files:
                course = form.save(commit=False)
                course.owner = self.request.user
                course.slug = slugify(data['name'])
                
                self.storage.extra_data['course_id'] = course.id
            else:
                messages.error(self.request, f"Error creating course: {e}")
                return  # The wizard will re-render the form and show the error

        elif step == 'topics':
            # Parse all topics from POST data
            data = self.request.POST
            topics = []
            i = 0
            while True:
                name = data.get(f'name_{i}')
                description = data.get(f'description_{i}')
                if not name:
                    break
                topics.append({'name': name, 'description': description})
                i += 1
            if course:
                try:
                    for idx, topic in enumerate(topics):
                        Topic.objects.create(
                            course=course,
                            name=topic['name'],
                            description=topic['description'],
                            order=idx+1
                        )
                except Exception as e:
                    messages.error(self.request, f"Error creating topics: {e}")
                    return  # The wizard will re-render the form and show the error
            else:
                messages.error(self.request, "Course not found. Cannot create topics.")
                return  # The wizard will re-render the form and show the error

        elif step == 'contents':
            # Support multiple contents if needed
            data = self.request.POST
            files = self.request.FILES
            i = 0
            has_any = False
            while True:
                topic_id = data.get(f'topic_{i}')
                content_type_id = data.get(f'content_type_{i}')
                order = data.get(f'order_{i}')
                if not topic_id or not content_type_id:
                    break
                # Build a form for each content
                content_form_data = {
                    'topic': topic_id,
                    'content_type': content_type_id,
                    'order': order,
                    'text_content': data.get(f'text_content_{i}'),
                    'file_content': files.get(f'file_content_{i}'),
                    'image_content': files.get(f'image_content_{i}'),
                    'video_file': files.get(f'video_file_{i}'),
                    'video_url': data.get(f'video_url_{i}'),
                }
                form = CourseTopicContentsForm(content_form_data, files)
                if form.is_valid():
                    form.save(owner=self.request.user)
                has_any = True
                i += 1
            # fallback for single content
            if not has_any and 'topic' in data:
                form = CourseTopicContentsForm(data, files)
                if form.is_valid():
                    form.save(owner=self.request.user)

        elif step == 'assignments':
            data = self.request.POST
            files = self.request.FILES
            form.fields['topic'].queryset = Topic.objects.filter(course=course)
            i = 0
            has_any = False
            while True:
                title = data.get(f'title_{i}')
                description = data.get(f'description_{i}')
                topic_id = data.get(f'topic_{i}')
                file = files.get(f'file_{i}')
                if not title:
                    break
                assignment = Assignment.objects.create(
                    title=title,
                    description=description,
                    topic_id=topic_id,
                    course=course,
                    file=file if file else None
                )
                # Handle rubric criteria for this assignment
                rubric_criteria = data.getlist(f'rubric_criteria_{i}[]')
                rubric_description = data.getlist(f'rubric_descriptions_{i}[]')
                rubric_max_scores = data.getlist(f'rubric_max_scores_{i}[]')
                for crit, desc, max_score in zip(rubric_criteria, rubric_description, rubric_max_scores):
                    Rubric.objects.create(
                        assignment=assignment,
                        criteria=crit,
                        description=desc,
                        max_score=max_score
                    )
                has_any = True
                i += 1
            # fallback for single assignment (non-indexed)
            if not has_any and 'title' in data:
                assignment = form.save(commit=False)
                assignment.course = course
                assignment.save()
                rubric_criteria = data.getlist('rubric_criteria[]')
                rubric_description = data.getlist('rubric_descriptions[]')
                rubric_max_scores = data.getlist('rubric_max_scores[]')
                for crit, desc, max_score in zip(rubric_criteria, rubric_description, rubric_max_scores):
                    Rubric.objects.create(
                        assignment=assignment,
                        criteria=crit,
                        description=desc,
                        max_score=max_score
                    )



        elif step == 'assessments':

            data = self.request.POST
            files = self.request.FILES
            form.fields['topic'].queryset = Topic.objects.filter(course=course)
            options_valid = True
            questions_data = []

            # Parse questions and options
            for key in data:
                if key.startswith('questions[') and key.endswith('][text]'):
                    q_index = key.split('[')[1].split(']')[0]
                    question_text = data.get(f'questions[{q_index}][text]')
                    explanation = data.get(f'questions[{q_index}][explanation]')

                    options = []
                    option_index = 1
                    while True:
                        opt_text = data.get(f'questions[{q_index}][options][{option_index}][text]')
                        if not opt_text:
                            break
                        is_correct = data.get(f'questions[{q_index}][options][{option_index}][is_correct]')
                        options.append({
                            'text': opt_text,
                            'is_correct': is_correct == 'true' or is_correct == 'on',
                            'order': option_index
                        })
                        option_index += 1
                    questions_data.append({
                        'text': question_text,
                        'explanation': explanation,
                        'options': options
                    })

            # Validation
            for q in questions_data:
                if len(q['options']) < 2:
                    options_valid = False
                    messages.error(self.request, "Please provide at least two options for each question.")
                if not any(opt['is_correct'] for opt in q['options']):
                    options_valid = False
                    messages.error(self.request, "Please select at least one correct option for each question.")

            # Deduplication
            unique_questions = []
            seen_questions = set()
            for q in questions_data:
                q_text = (q['text'] or '').strip().lower()
                if q_text and q_text not in seen_questions:
                    # Deduplicate options for this question by option_text
                    unique_options = []
                    seen_options = set()
                    for opt in q['options']:
                        opt_text = (opt['text'] or '').strip().lower()
                        if opt_text and opt_text not in seen_options:
                            unique_options.append(opt)
                            seen_options.add(opt_text)
                    q['options'] = unique_options
                    unique_questions.append(q)
                    seen_questions.add(q_text)
            questions_data = unique_questions

            # If validation fails, return early (do not save)
            if not options_valid or not questions_data:
                return  # The wizard will re-render the form and show messages

            # Save to DB atomically
            try:
                with transaction.atomic():
                    assessment = form.save(commit=False)
                    assessment.course = course
                    assessment.created_by = self.request.user
                    assessment.save()

                    for q in questions_data:
                        question = AssessmentQuestion.objects.create(
                            assessment=assessment,
                            text=q['text'],
                            explanation=q['explanation']
                        )
                        for opt in q['options']:
                            MCQOption.objects.create(
                                question=question,
                                option_text=opt['text'],
                                is_correct=opt['is_correct'],
                                order=opt['order']
                            )
            except Exception as e:
                messages.error(self.request, f"An error occurred while saving the assessment: {e}")
                return  # The wizard will re-render the form and show messages




        elif step == 'marketing':
            data = form.cleaned_data
            other_data = self.request.POST
            files = self.request.FILES

            trailer_form = CourseTrailerForm(other_data, files=files)
            form.save()

            # Accept multiple objectives and requirements
            objectives = other_data.getlist('objectives[]') or [
                v for k, v in other_data.items() if k.startswith('objective_')
            ]
            requirements = other_data.getlist('requirements[]') or [
                v for k, v in other_data.items() if k.startswith('requirement_')
            ]

            if trailer_form.is_valid() and form.is_valid():
                with transaction.atomic():
                    # Save trailer
                    trailer = trailer_form.save(commit=False)
                    trailer.course = course
                    trailer.save()

                    # Save multiple requirements
                    for req in requirements:
                        req = req.strip()
                        if req:
                            CourseRequirements.objects.create(course=course, requirement=req)

                    # Save multiple objectives
                    for obj in objectives:
                        obj = obj.strip()
                        if obj:
                            CourseObjectives.objects.create(course=course, objective=obj)


    def done(self, form_list, **kwargs):
        course_id = self.storage.extra_data.get('course_id')
        course = Course.objects.get(id=course_id)
        messages.success(self.request, "Course created successfully!")
        return redirect('course:course', course_slug=course.slug)
    



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
    total_topics = topic.course.course_topics.count()
    topics_check = topic.course.course_topics.all()
    # Get the student's enrollment for this course
    enrollment = Enrollment.objects.filter(student=request.user, course=topic.course).first()

    if enrollment:
        completed_topics_count = enrollment.completed_topics.count()
    else:
        completed_topics_count = 0
    course_completed = False  # Initialize with a default value
    if not topics_check.filter(is_completed=False):
        course_completed = True

    contents = Content.objects.prefetch_related('content_type').filter(topic=topic)
    assignments = topic.course.assignments.filter(topic=topic)
    assignment = topic.course.assignments.first()  # Example: Get the first assignment
    assignment_user_tasks = {
        a.id: UserTask.objects.filter(task=a.assignment_task, user=request.user).first()
        for a in assignments
    }
    total_completed_assignments = UserTask.objects.filter(
        user=request.user,
        task__assignment__in=assignments,
        is_completed=True
    ).count()
    print(total_completed_assignments)
    assessments = topic.course.assessments.filter(topic=topic)
    assessment_user_tasks = {
        a.id: UserTask.objects.filter(task=a.assessment_task, user=request.user).first()
        if hasattr(a, 'assessment_task') else None
        for a in assessments
    }
    total_completed_assessments = UserTask.objects.filter(
        user=request.user,
        task__assessment__in=assessments,
        is_completed=True
    ).count()
    assignment_total = assignments.count()
    assessment_total = assessments.count()
    total_tasks = assignment_total + assessment_total

    total_completed_tasks = total_completed_assessments + total_completed_assignments
    if total_tasks > 0:
        topic_completion_percentage = int((float(total_completed_tasks)/float(total_tasks))*100)
    else:
        topic_completion_percentage = 0
    
    # Get the ContentType for the Video model
    video_content_type = ContentType.objects.get_for_model(Video)

    # Filter by the ContentType instance
    video_count = contents.filter(content_type=video_content_type).count()


    context = {
               'topic': topic, 'completed_topics_count':completed_topics_count,
               'contents': contents, 'total_topics':total_topics,
               'assignment_user_tasks':assignment_user_tasks, 'video_count': video_count, 
               'assignments': assignments, 'now': now, 'assessments':assessments,
               'course_commpleted':course_completed, 'total_completed_assignments':total_completed_assignments,
               'topic_completion_percentage':topic_completion_percentage,
               'total_completed_assessments':total_completed_assessments, 'assessment_user_tasks':assessment_user_tasks
               }
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
def manage_courses(request):
    courses = Course.objects.filter(owner=request.user)
    context = {'courses': courses}
    return render(request, 'courses/manage/manage_courses.html', context)



@login_required
def create_assignment(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = AssignmentForm(request.POST, request.FILES, user=request.user)
        form.fields['topic'].queryset = Topic.objects.filter(course=course)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.is_graded = False
            assignment.save()
            rubric_criteria = request.POST.getlist('rubric_criteria[]')
            rubric_description = request.POST.getlist('rubric_description[]')
            rubric_max_score = request.POST.getlist('rubric_max_score[]')

            for crit, desc, max_score in zip(rubric_criteria, rubric_description, rubric_max_score):
                Rubric.objects.create(
                    assignment=assignment,
                    criteria=crit,
                    description=desc,
                    max_score=max_score
                )
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
        form.fields['topic'].queryset = Topic.objects.filter(course=course)
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
            submission.save()
            Submission.handle_submission_side_effects(submission)
            
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






@login_required
def assignment_detail(request, course_id, topic_id, assignment_id):
    course = get_object_or_404(Course, id=course_id)
    topic = get_object_or_404(Topic, id=topic_id, course=course)
    assignment = get_object_or_404(Assignment, id=assignment_id, topic=topic)
    is_instructor = course.owner == request.user
    
    context = {
        'course': course,
        'topic': topic,
        'assignment': assignment,
        'is_instructor': is_instructor,
    }
    
    if is_instructor:
        # Instructor view data
        submissions = Submission.objects.filter(assignment=assignment).select_related('user')
        total_students = course.students.count()
        
        context.update({
            'submissions': submissions,
            'total_students': total_students,
        })
    else:
        # Student view data
        user_submission = Submission.objects.filter(
            assignment=assignment,
            user=request.user
        ).first()
        
        context.update({
            'user_submission': user_submission,
        })
    
    return render(request, 'students/manage/assignment_detail.html', context)

def grade_assignments(request):
    assignments = Assignment.objects.filter(course__owner=request.user)
    submissions = Submission.objects.filter(assignment__in=assignments)

    assignment_id = request.GET.get('assignment')
    status = request.GET.get('status')

    if assignment_id:
        submissions = submissions.filter(assignment__id=assignment_id)
    if status:
        filtered_ids = [
            s.id for s in submissions
            if UserTask.objects.filter(
                task=s.assignment.assignment_task,
                user=s.user,
                status=status
            ).exists()
        ]
        submissions = submissions.filter(id__in=filtered_ids)
    


    user_task_statuses = {
        s.id: UserTask.objects.filter(task=s.assignment.assignment_task, user=s.user).first().status
        for s in submissions
    }
    all_statuses = [choice[0] for choice in UserTask.AssignmentStatus]

    context = {'submissions':submissions, 'assignments':assignments, 
               'user_task_statuses':user_task_statuses, 'all_statuses':all_statuses, 
               'selected_assignment':assignment_id, 'selected_status':status,
               }
    return render(request, 'students/manage/grade_assignments.html', context)

def get_submission_details(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)

    # Ensure a Grade exists for this submission
    grade, created = Grade.objects.get_or_create(
        submission=submission,
        defaults={'user': submission.user, 'score': 0}
    )
    
    # Handle files
    files = submission.files.all() if hasattr(submission, 'files') else []

    # Check if the submission has a grade
    if hasattr(submission, 'submission_grade'):
        rubric_items = submission.assignment.rubrics.all()
        feedback = grade.feedback
        current_grade = grade.score
    else:
        rubric_items = []
        feedback = ''
        current_grade = None



    data = {
        'student_name': submission.user.full_name,
        'assignment_title': submission.assignment.title,
        'submitted_at': submission.submitted_at.strftime('%b %d, %Y %H:%M'),
        'is_late': submission.assignment.is_past_due,
        'max_points': submission.assignment.max_score,
        'current_grade': current_grade,
        'content': submission.content,
        'feedback': feedback,
        'files_url': [f.file.url for f in files] if files else [],
        'rubric': [
            {
                'criterion': item.criteria,
                'max_points': item.max_score,
                'current_points': item.rubric_scores.filter(submission=submission).first().score if item.rubric_scores.filter(submission=submission).exists() else None,
                'description': item.description,
                'id': str(item.id),
            } for item in rubric_items
        ],

    }
    print(submission.user.full_name)
    print(submission.assignment.title)
    print(submission.submitted_at.strftime('%b %d, %Y %H:%M'))
    print(submission.assignment.is_past_due)
    return JsonResponse(data, safe=False)


def grade_submissions(request, submission_id):
    submission = get_object_or_404(Submission, id=submission_id)
    grade = float(request.POST.get('grade', 0))
    feedback = request.POST.get('feedback', '')
    rubric_scores = request.POST.getlist('rubric_scores[]')
    rubric_ids = request.POST.getlist('rubric_ids[]')

    try:
        submission.grade = grade
        submission.save()
        submission.assignment.is_graded = True
        submission.assignment.save()
        # Update rubric scores
        for rubric_id, score in zip(rubric_ids, rubric_scores):
            rubric = submission.assignment.rubrics.get(id=rubric_id)
            RubricScore.objects.update_or_create(
                rubric=rubric,
                submission=submission,
                defaults={'score': score}
            )
    
        # Update feedback, etc.
        submission.submission_grade.feedback = feedback
        submission.submission_grade.score = grade
        submission.submission_grade.save()
        

        Notification.objects.create(
            recipient=submission.user,
            notification_type='Graded',
            title=f"Assignment grading: {submission.assignment.title}",
            message=f"Your {submission.assignment.title}'s assignment have been graded",
            related_course=submission.assignment.course,
            is_read=False
        )
        
        # Create notification for instructor
        Notification.objects.create(
            recipient=submission.assignment.course.owner,
            notification_type='Graded',
            title=f"Assignment grading: {submission.assignment.title}",
            message=f"You have successfully graded {submission.user.full_name}'s {submission.assignment.title}",
            related_course=submission.assignment.course,
            is_read=False
        )
    
    
        return JsonResponse({
            'success': True,
            'status_display': 'Graded',
            'grade': submission.grade,
            'max_points': submission.assignment.max_score,
            'status': 'graded',  # if you want to update the badge
            'updated_data': {
                'status': 'graded',
                'status_display': 'Graded',
                'grade': submission.grade,
                'max_points': submission.assignment.max_score,
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})


#ASSESSMENT

def create_assessment(request, course_id):
    course = get_object_or_404(Course, id=course_id)

    if request.method == 'POST':
        form = AssessmentForm(request.POST)
        form.fields['topic'].queryset = Topic.objects.filter(course=course)
        options_valid = True
        questions_data = []
        
        for key in request.POST:
            if key.startswith('questions[') and key.endswith('][text]'):
                q_index = key.split('[')[1].split(']')[0]
                question_text = request.POST.get(f'questions[{q_index}][text]')
                explanation = request.POST.get(f'questions[{q_index}][explanation]')
                # Gather options for this question
                options = []
                option_index = 1
                while True:
                    opt_text = request.POST.get(f'questions[{q_index}][options][{option_index}][text]')
                    if not opt_text:
                        break
                    is_correct = request.POST.get(f'questions[{q_index}][options][{option_index}][is_correct]')
                    options.append({
                        'option_text': opt_text,
                        'is_correct': is_correct == 'true' or is_correct == 'on',
                        'order': option_index
                    })
                    option_index += 1
                questions_data.append({
                    'text': question_text,
                    'explanation': explanation,
                    'options': options
                })

        # Validate questions and options
        for q in questions_data:
            if len(q['options']) < 2:
                options_valid = False
                messages.error(request, "Please provide at least two options for each question.")
            if not any(opt['is_correct'] for opt in q['options']):
                options_valid = False
                messages.error(request, "Please select at least one correct option for each question.")
        
        # Remove duplicate questions by text (case-insensitive)
        unique_questions = []
        seen_questions = set()
        for q in questions_data:
            q_text = (q['text'] or '').strip().lower()
            if q_text and q_text not in seen_questions:
                # Deduplicate options for this question by option_text
                unique_options = []
                seen_options = set()
                for opt in q['options']:
                    opt_text = (opt['option_text'] or '').strip().lower()
                    if opt_text and opt_text not in seen_options:
                        unique_options.append(opt)
                        seen_options.add(opt_text)
                q['options'] = unique_options
                unique_questions.append(q)
                seen_questions.add(q_text)
        questions_data = unique_questions

        if form.is_valid() and options_valid and questions_data:
            assessment = form.save(commit=False)
            assessment.course = course
            assessment.created_by = request.user
            assessment.save()
            for q in questions_data:
                question = AssessmentQuestion.objects.create(
                    assessment=assessment,
                    question=q['text'],
                    explanation=q['explanation']
                )
                for opt in q['options']:
                    MCQOption.objects.create(
                        question=question,
                        option_text=opt['option_text'],
                        is_correct=opt['is_correct'],
                        order=opt['order']
                    )
            messages.success(request, "Assessment created successfully!")
            return redirect('course:course', course.slug)
        # else: errors will be shown

    else:
        form = AssessmentForm(initial={'points': 1, 'time_limit': 5})
        form.fields['topic'].queryset = Topic.objects.filter(course=course)
    return render(request, 'students/manage/create_assessments.html', {'form': form, 'course': course})


@login_required
def attempt_assessment(request, assessment_id):
    assessment = get_object_or_404(Assessment, id=assessment_id)
    questions_list = assessment.questions.prefetch_related('options').all()
    
    # Check for existing completed attempt
    existing_attempt = AssessmentAttempt.objects.filter(
        user=request.user, 
        assessment=assessment, 
        is_completed=True
    ).first()
    
    if existing_attempt:
        messages.info(request, "You have already completed this assessment.")
        return redirect('course:assessment_result', attempt_id=existing_attempt.id)
    
    # Paginate questions (1 per page)
    paginator = Paginator(questions_list, 1)
    page_number = request.GET.get('page', 1)
    questions = paginator.get_page(page_number)
    
    # Get answered pages for pagination styling
    answered_pages = []
    if request.method == 'POST':
        # Handle form submission
        attempt, created = AssessmentAttempt.objects.get_or_create(
            user=request.user,
            assessment=assessment,
            defaults={'started_at': now()}
        )
        
        # Process the answer
        question_id = request.POST.get('question_id')
        if question_id:
            question = get_object_or_404(AssessmentQuestion, id=question_id)
            selected_option_id = request.POST.get(f'question_{question_id}')
            
            if selected_option_id:
                selected_option = get_object_or_404(MCQOption, id=selected_option_id)
                
                # Save or update response
                MCQResponse.objects.update_or_create(
                    attempt=attempt,
                    question=question,
                    defaults={
                        'selected_option': selected_option,
                        'is_correct': selected_option.is_correct
                    }
                )
        
        # Check if this is a final submission
        if 'finish' in request.POST:
            # Calculate score
            responses = attempt.responses.all()
            total_questions = assessment.questions.count()
            correct_count = responses.filter(is_correct=True).count()
            score = (correct_count / total_questions) * 100 if total_questions > 0 else 0
            
            # Complete the attempt
            attempt.score = score
            attempt.completed_at = now()
            attempt.is_completed = True
            attempt.save()
            AssessmentAttempt.handle_assessment_attempt_side_effects(attempt)
            
            messages.success(request, f"Assessment submitted! Your score: {score:.2f}%")
            return redirect('course:assessment_result', attempt_id=attempt.id)
        
        # For AJAX requests (next question)
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
    
    # Get answered pages for pagination styling
    if request.user.is_authenticated:
        attempt = AssessmentAttempt.objects.filter(
            user=request.user,
            assessment=assessment
        ).first()
        
        if attempt:
            answered_pages = list(attempt.responses.values_list(
                'question__id', flat=True
            ))
            answered_pages = [i for i, q in enumerate(questions_list, 1) if q.id in answered_pages]
    
    return render(request, 'students/manage/attempt_assessment.html', {
        'assessment': assessment,
        'questions': questions,
        'answered_pages': answered_pages,
        'test_duration': assessment.time_limit * 60  # Convert to seconds
    })


@login_required
def assessment_result(request, attempt_id):
    attempt = get_object_or_404(AssessmentAttempt, id=attempt_id, user=request.user)
    assessment = attempt.assessment

    # Calculate correct/incorrect counts
    responses = attempt.responses.select_related('question', 'selected_option')
    correct_count = responses.filter(is_correct=True).count()
    incorrect_count = responses.filter(is_correct=False).count()

    # Calculate completion time (if available)
    if attempt.completed_at and attempt.started_at:
        delta = attempt.completed_at - attempt.started_at
        minutes, seconds = divmod(int(delta.total_seconds()), 60)
        if minutes:
            completion_time = f"{minutes} min {seconds} sec"
        else:
            completion_time = f"{seconds} sec"
    else:
        completion_time = "N/A"

    return render(request, 'students/manage/assessment_result.html', {
        'assessment': assessment,
        'attempt': attempt,
        'correct_count': correct_count,
        'incorrect_count': incorrect_count,
        'completion_time': completion_time,
    })