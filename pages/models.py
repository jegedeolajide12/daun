from django.db import models
from django.shortcuts import redirect
from django.urls import reverse
from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from .fields import OrderField

from accounts.models import CustomUser

User = get_user_model()
# Create your models here.

class Faculty(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'faculties'
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.name


class CourseManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().filter(published=True, is_active=True)

    
class Course(models.Model):
    class AudienceType(models.TextChoices):
        BEGINNER = 'beginner', _('Beginner')
        INTERMEDIATE = 'intermediate', _('Intermediate')
        ADVANCED = 'advanced', _('Advanced')
        ALL = 'all', _('All Levels')
    
    class PriceTier(models.TextChoices):
        FREE = 'free', _('Free')
        TIER_1000 = '1000', _('1,000')
        TIER_3000 = '3000', _('3,000')
        TIER_5000 = '5000', _('5,000')
        TIER_10000 = '10000', _('10,000')
        TIER_30000 = '30000', _('30,000')
        TIER_50000 = '50000', _('50,000')


    students = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Enrollment', related_name='courses_joined', blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='courses_created', on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, related_name='faculty_courses', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    code = models.CharField(max_length=6, null=True, blank=True)
    cover_image = models.ImageField(null=True, upload_to='courses/cover_images')
    overview = models.TextField()
    price_tier = models.CharField(max_length=20, choices=PriceTier.choices, default=PriceTier.FREE)
    discount_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created = models.DateTimeField(auto_now_add=True)
    is_completed = models.BooleanField(default=False)
    published = models.BooleanField(default=False)
    updated = models.DateTimeField(auto_now=True)
    audience = models.CharField(max_length=20, choices=AudienceType.choices, default=AudienceType.ALL)
    objects = CourseManager()
    all_objects = models.Manager()
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created']
    
    def get_absolute_url(self):
        return reverse('course:course', args=[self.slug])
        
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class CourseTrailer(models.Model):
    course = models.OneToOneField(Course, related_name='trailer', on_delete=models.CASCADE)
    video_url = models.URLField(null=True, blank=True)
    file = models.FileField(upload_to='course_trailers', null=True, blank=True)

    class Meta:
        verbose_name_plural = 'Course Trailers'
        ordering = ['course']

    def __str__(self):
        return f'Trailer for {self.course.name}'


class CourseRequirements(models.Model):
    course = models.ForeignKey(Course, related_name='requirements', on_delete=models.CASCADE)
    requirement = models.TextField()

    class Meta:
        verbose_name_plural = 'Course Requirements'
        ordering = ['course']

    def __str__(self):
        return f'Requirements for {self.course.name}'


class CourseObjectives(models.Model):
    course = models.ForeignKey(Course, related_name='objectives', on_delete=models.CASCADE)
    objective = models.TextField()

    class Meta:
        verbose_name_plural = 'Course Objectives'
        ordering = ['course']

    def __str__(self):
        return f'Objectives for {self.course.name}'

class Topic(models.Model):
    course = models.ForeignKey(Course, related_name='course_topics', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])
    is_completed = models.BooleanField(default=False)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.order}. {self.name}'


class Content(models.Model):
    topic = models.ForeignKey(Topic, related_name='contents', on_delete=models.CASCADE)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, limit_choices_to={'model__in':('text','image','video','file')})
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')
    order = OrderField(blank=True, for_fields=['topic'])

    class Meta:
        ordering = ['order']


class ItemBase(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='%(class)s_related', on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
    
    def __str__(self):
        return self.title

class Text(ItemBase):
    content = models.TextField()

class File(ItemBase):
    file = models.FileField(upload_to='files')

class Image(ItemBase):
    file = models.FileField(upload_to='images')

class Video(ItemBase):
    url = models.URLField(null=True, blank=True)
    file = models.FileField(upload_to='videos', null=True, blank=True)

    def has_video(self):
        return bool(self.file or self.url)

class TaskType(models.TextChoices):
    QUIZ = 'quiz', 'Quiz'
    ASSIGNMENT = 'assignment', 'Assignment'
    ASSESSMENT = 'assessment', 'Assessment'
    EXAM = 'exam', 'Exam'
    PROJECT = 'project', 'Project'

class Task(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_tasks')
    start_date = models.DateTimeField()
    due_date = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.QUIZ)
    assignment = models.OneToOneField('Assignment', on_delete=models.CASCADE, related_name='assignment_task', null=True,blank=True)
    assessment = models.OneToOneField('Assessment', on_delete=models.CASCADE, related_name='assessment_task', null=True, blank=True)
    description = models.TextField()

    def __str__(self):
        return f'{self.title} - {self.course.name}'
    def save(self, *args, **kwargs):
        # Save the Task instance first to ensure it has a primary key
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

        # Now create UserTask objects for all students in the course
        students = self.course.students.all()
        existing_user_tasks = UserTask.objects.filter(task=self).values_list('user_id', flat=True)
        user_tasks = [
            UserTask(user=student, task=self) for student in students if student.id not in existing_user_tasks
        ]
        UserTask.objects.bulk_create(user_tasks)


class UserTask(models.Model):
    AssignmentStatus = (
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('graded', 'Graded'),
        ('overdue', 'Overdue'),
    )
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='user_tasks')
    is_completed = models.BooleanField(default=False)
    score = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=AssignmentStatus, default='pending')

    
    class Meta:
        ordering = ['is_completed' ,'task__due_date']


    def get_average_score(self):
        return UserTask.objects.filter(task=self.task).aggregate(Avg('score'))['score__avg']

    def get_gpa(self, user=None):
        if user is None:
            user = self.user
        graded_tasks = user.user_tasks.filter(score__isnull=False)

        if not graded_tasks.exists():
            return 0.0  # No GPA yet

        total_quality_points = 0
        total_units = 0

        for task_score in graded_tasks:
            score = task_score.score
            unit = 3  # assumed course unit

            if score >= 70:
                grade_point = 5
            elif score >= 60:
                grade_point = 4
            elif score >= 50:
                grade_point = 3
            elif score >= 45:
                grade_point = 2
            elif score >= 40:
                grade_point = 1
            else:
                grade_point = 0

            total_quality_points += grade_point * unit
            total_units += unit

        if total_units == 0:
            return 0.0

        return round(total_quality_points / total_units, 2)



    def __str__(self):
        return f'{self.user.username} - {self.task.title}'
    
class Enrollment(models.Model):
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    date_enrolled = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    progress = models.IntegerField(default=0)  # Progress in percentage
    last_activity = models.DateTimeField(auto_now=True, null=True, blank=True)
    completed_topics = models.ManyToManyField(Topic, related_name='completed_by', blank=True)
    average_score = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-date_enrolled']
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  # Save the Enrollment instance first
        self.course.students.add(self.student)
        self.course.save()
        for task in self.course.course_tasks.all():
            UserTask.objects.get_or_create(user=self.student, task=task)
        
        
            


    
    def get_progress(self):
        total_topics = self.course.course_topics.count()
        completed_topics = self.completed_topics.count()
        if total_topics == 0:
            return 0
        return int((completed_topics / total_topics) * 100)
    
    def delete(self, *args, **kwargs):
        # Remove the student from the course's students list
        self.course.students.remove(self.student)
        super().delete(*args, **kwargs)

    def __str__(self):
        return f'{self.student.username} enrolled in {self.course.name}'


class StudentActivity(models.Model):
    ACTIVITY_TYPES = (
        ('module_complete', 'Module Completed'),
        ('quiz_attempt', 'Quiz Attempt'),
        ('assignment_submit', 'Assignment Submitted'),
        ('forum_post', 'Forum Post'),
        ('message', 'Message Sent'),
    )
    
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='activities')
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES)
    title = models.CharField(max_length=200)
    details = models.TextField(blank=True)
    timestamp = models.DateTimeField(default=timezone.now)

    def get_icon_class(self):
        icons = {
            'module_complete': 'fas fa-check-circle',
            'quiz_attempt': 'fas fa-question-circle',
            'assignment_submit': 'fas fa-file-upload',
            'forum_post': 'fas fa-comments',
            'message': 'fas fa-envelope',
        }
        return icons.get(self.activity_type, 'fas fa-circle')

class Assignment(models.Model):
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    topic = models.ForeignKey(Topic, on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    description = models.TextField()
    file = models.FileField(upload_to='assignments', null=True, blank=True)
    max_score = models.IntegerField(default=100)
    is_graded = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.pk:
            self.status = 'pending'
            self.is_graded = False
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
        # Create Task objects so that UserTask can be created for all students in the course
        title = self.title
        task, created = Task.objects.get_or_create(
            assignment=self,
            title=title,
            course=self.course,
            start_date=self.created,
            due_date=self.due_date,
            type=TaskType.ASSIGNMENT,
            description=self.description
        )
    @property
    def is_past_due(self):
        return timezone.now() > self.due_date
    
    @property
    def is_active(self):
        return not self.is_past_due
    

    def get_absolute_url(self):
        return reverse('course:assignment_detail', kwargs={
            'assignment_id': self.id,
            'topic_id': self.topic.id,
            'course_id': self.course.id
        }) 

    def __str__(self):
        return f'Assignment: {self.title} for {self.course.name}'

class Submission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    assignment = models.OneToOneField(Assignment, related_name='assignment_submission', on_delete=models.CASCADE, null=True, blank=True)
    content = models.TextField(null=True, blank=True)
    grade = models.PositiveIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        
        super().save(*args, **kwargs)
    
    def handle_submission_side_effects(submission):
        """
        Call this after saving a Submission to handle UserTask and topic completion logic.
        """
        assignment = submission.assignment
        user = submission.user
        if not assignment:
            return
        task = getattr(assignment, 'assignment_task', None)
        if task:
            user_task = UserTask.objects.filter(user=user, task=task).first()
            if user_task:
                user_task.is_completed = True
                user_task.status = 'submitted'
                user_task.save()
        course = assignment.course
        topic = assignment.topic
        enrollment = Enrollment.objects.filter(student=user, course=course).first()
        if enrollment and topic:
            # Check all assignments
            all_assignments_completed = all(
                UserTask.objects.filter(user=user, task=a.assignment_task, is_completed=True).exists()
                for a in topic.assignments.all()
            )
            # Check all assessments
            all_assessments_completed = all(
                AssessmentAttempt.objects.filter(user=user, assessment=assess, is_completed=True).exists()
                for assess in topic.assessments.all()
            )
            if all_assignments_completed and all_assessments_completed:
                topic.is_completed = True
                topic.save()
                enrollment.completed_topics.add(topic)
        StudentActivity.objects.create(
            user=user,
            course=course,
            activity_type='assignment_submit',
            title=f'Assignment Submitted: {assignment.title}',
            details=f'Assignment \"{assignment.title}\" submitted by {user.username}.'
        )

    def delete(self, *args, **kwargs):
        # Set the assignment status to 'pending' if the submission is deleted
        if self.assignment:
            self.assignment.is_graded = False
            self.assignment.save()

        task = self.assignment.assignment_task
        # Mark the UserTask as not completed
        user_task = UserTask.objects.filter(user=self.user, task__assignment=self.assignment).first()
        if user_task:
            user_task.is_completed = False
            user_task.status = 'pending'
            user_task.save()
        
        super().delete(*args, **kwargs)
    
    @property
    def is_graded(self):
        return self.grade is not None

    def __str__(self):
        return f'Submission by {self.user.username} for {self.assignment.title}'

    def clean(self):
        if not self.files and not self.content:
            raise ValidationError('Either a file or content must be provided.')
    @property
    def get_status(self):
        user_task = UserTask.objects.filter(
            user=self.user, 
            task=self.assignment.assignment_task
            ).first()
        if user_task:
            return user_task.status
        return 'pending'
        


class SubmissionFile(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='submissions/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.file.name
    
    def filename(self):
        return self.file.name.split('/')[-1]
    
    def delete(self, *args, **kwargs):
        # Delete the file from storage when model is deleted
        self.file.delete()
        super().delete(*args, **kwargs)


class Notification(models.Model):
    NOTIFICATION_TYPES = (
        ('enrollment', 'New Enrollment'),
        ('task', 'New Task Assigned'),
        ('deadline', 'Deadline Reminder'),
        ('submission', 'New Submission'),
        ('Assignment', 'New Assignment'),
        ('progress', 'Progress Update'),
        ('message', 'Message'),
        ('grade', 'Grade Update'),
        ('system', 'System Notification'),
    )
    recipient = models.ForeignKey(User, 
                                  on_delete=models.CASCADE, 
                                  related_name='notifications'
                                  )
    sender = models.ForeignKey(User, 
                                on_delete=models.CASCADE, 
                                related_name='sent_notifications', 
                                null=True, 
                                blank=True,
                                )
    notification_type = models.CharField(max_length=20, 
                                         choices=NOTIFICATION_TYPES
                                         )
    title = models.CharField(max_length=200)
    message = models.TextField()
    related_course = models.ForeignKey(Course, 
                                        on_delete=models.SET_NULL,
                                        related_name='notifications',
                                        null=True,
                                        blank=True,
                                        )
    related_enrollment = models.ForeignKey(Enrollment,
                                        on_delete=models.SET_NULL,
                                        related_name='notifications',
                                        null=True,
                                        blank=True,
                                        )
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
        ]
    def __str__(self):
        return f'{self.notification_type.upper()}: {self.title}'
    def mark_as_read(self):
        self.is_read = True
        self.save()



class Grade(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='grades')
    submission = models.OneToOneField(Submission, on_delete=models.CASCADE, related_name='submission_grade')
    score = models.IntegerField()
    feedback = models.TextField(null=True, blank=True)
    graded_at = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        # Update the submission's grade when a new grade is saved
        self.submission.grade = self.score
        self.submission.save()
        self.assignment.is_graded = True
        self.assignment.save()
        self.assignment.assignment_task.is_completed = True
        self.assignment.assignment_task.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.user.username} - {self.submission.assignment.title} - {self.score}'


class Rubric(models.Model):
    description = models.TextField()
    criteria = models.TextField()
    max_score = models.IntegerField(default=100)
    score = models.IntegerField(null=True, blank=True)
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='rubrics')


    def __str__(self):
        return f'Rubric for {self.assignment.title}'

class RubricScore(models.Model):
    rubric = models.ForeignKey(Rubric, on_delete=models.CASCADE, related_name='rubric_scores')
    score = models.IntegerField(null=True, blank=True)
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE, related_name='rubric_scores')

    def save(self, *args, **kwargs):
        self.rubric.score = self.score
        self.rubric.save()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f'{self.user.username} - {self.rubric.assignment.title} - {self.score}'

class Assessment(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_assessments', null=True, blank=True)
    points = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Points"),
        help_text=_("Points awarded for correct answer")
    )
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    due_date = models.DateTimeField(null=True, blank=True)
    time_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Time Limit (seconds)"),
        help_text=_("Time limit for this question in seconds")
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='assessments'
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name='assessments',
        null=True,
        blank=True
    )

    class Meta:
        verbose_name = _("Assessment")
        verbose_name_plural = _("Assessments")
        constraints = [
            models.CheckConstraint(
                check=models.Q(points__gte=1),
                name="points_gte_1"
            )
        ]

    def __str__(self):
        return f"Assessment for {self.course.name} (ID: {self.id})"

    def clean(self):
        if self.due_date and self.due_date < timezone.now():
            raise ValidationError(_("Due date cannot be in the past."))
        if self.time_limit and self.time_limit <= 0:
            raise ValidationError(_("Time limit must be positive."))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        title = f"Assessment for {self.course.name} (ID: {self.id})"
        task, created = Task.objects.get_or_create(
            assessment=self,
            title=title,
            course=self.course,
            start_date=self.created,
            due_date=self.due_date,
            type=TaskType.ASSESSMENT,
            description=getattr(self, 'description', '')
        )
    
    def get_absolute_url(self):
        return reverse('course:create_assessment', args=[self.id])


class AssessmentQuestion(models.Model):
    question = models.TextField(
        verbose_name=_("Question Text"),
        help_text=_("Enter the question text in full"),
    )
    explanation = models.TextField(
        blank=True,
        null=True,
        verbose_name=_("Explanation"),
        help_text=_("Explanation to be shown after answering")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this question is active for use")
    )
    assessment = models.ForeignKey(Assessment, related_name='questions', on_delete=models.CASCADE)
    order = OrderField(blank=True, for_fields=['assessment'])

    class Meta:
        ordering = ['order']
        verbose_name = _("Assessment Question")
        verbose_name_plural = _("Assessment Questions")
    
    def get_correct_options(self):
        return self.options.filter(is_correct=True)

    def validate_correct_options(self):
        correct_options = self.get_correct_options().count()
        if correct_options == 0:
            raise ValidationError(_("At least one option must be marked as correct."))

    

class MCQOption(models.Model):
    question = models.ForeignKey(
        AssessmentQuestion,
        on_delete=models.CASCADE,
        related_name='options',
        null=True, blank=True
    )
    option_text = models.TextField(
        verbose_name=_("Option Text")
    )
    is_correct = models.BooleanField(
        default=False,
        verbose_name=_("Is Correct")
    )
    order = OrderField(blank=True, for_fields=['question'])

    class Meta:
        verbose_name = _("MCQ Option")
        verbose_name_plural = _("MCQ Options")
        ordering = ['order']
        constraints = [
            models.UniqueConstraint(
                fields=['question', 'order'],
                name='unique_option_order_per_question'
            )
        ]

    def __str__(self):
        return f'Option {self.order} for {str(self.question)[:30]}'

    def clean(self):
        if not self.assessment:
            raise ValidationError(_('Assessment must be provided.'))
        if not self.option_text:
            raise ValidationError(_('Option text must be provided.'))
        if not isinstance(self.is_correct, bool):
            raise ValidationError(_('is_correct must be a boolean value.'))
        
        # Ensure at least one correct option exists (but not during initial creation)
        if self.pk and self.is_correct:
            other_correct = self.assessment.options.exclude(pk=self.pk).filter(is_correct=True).exists()
            if not other_correct and not self.is_correct:
                raise ValidationError(_('At least one option must be marked as correct.'))

class AssessmentAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    score = models.FloatField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        
        super().save(*args, **kwargs)
    
    def handle_assessment_attempt_side_effects(attempt):
        """
        Call this after saving an AssessmentAttempt to handle UserTask and topic completion logic.
        """
        assessment = attempt.assessment
        user = attempt.user
        task = getattr(assessment, 'assessment_task', None)
        if task:
            user_task = UserTask.objects.filter(user=user, task=task).first()
            if user_task:
                user_task.is_completed = True
                user_task.status = 'submitted'
                user_task.save()
        # Only check when marking as completed
        if attempt.is_completed:
            topic = assessment.topic
            course = assessment.course
            enrollment = Enrollment.objects.filter(student=user, course=course).first()
            if enrollment and topic:
                assignments = list(topic.assignments.all())
                assessments = list(topic.assessments.all())
                # Check all assignments
                all_assignments_completed = all(
                    UserTask.objects.filter(user=user, task=a.assignment_task, is_completed=True).exists()
                    for a in assignments
                )
                # Check all assessments
                all_assessments_completed = all(
                    AssessmentAttempt.objects.filter(user=user, assessment=assess, is_completed=True).exists()
                    for assess in assessments
                )
                if all_assignments_completed and all_assessments_completed:
                    topic.is_completed = True
                    topic.save()
                    enrollment.completed_topics.add(topic)

        

class MCQResponse(models.Model):
    attempt = models.ForeignKey(AssessmentAttempt, on_delete=models.CASCADE, related_name='responses')
    question = models.ForeignKey(AssessmentQuestion, on_delete=models.CASCADE)
    selected_option = models.ForeignKey(MCQOption, on_delete=models.CASCADE, null=True, blank=True)
    is_correct = models.BooleanField(default=False)
    responded_at = models.DateTimeField(auto_now_add=True)