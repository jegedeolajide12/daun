from django.db import models
from django.db.models import Avg
from django.contrib.auth import get_user_model
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from .fields import OrderField

User = get_user_model()
# Create your models here.

class Faculty(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'faculties'
    
    def __str__(self):
        return self.name

    
class Course(models.Model):
    students = models.ManyToManyField(settings.AUTH_USER_MODEL, through='Enrollment', related_name='courses_joined', blank=True)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='courses_created', on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, related_name='faculty_courses', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    code = models.CharField(max_length=6, null=True, blank=True)
    cover_image = models.ImageField(null=True, upload_to='courses/cover_images')
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

class Topic(models.Model):
    course = models.ForeignKey(Course, related_name='course_topics', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    order = OrderField(blank=True, for_fields=['course'])

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
    EXAM = 'exam', 'Exam'
    PROJECT = 'project', 'Project'

class Task(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, null=True, blank=True)
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='course_tasks')
    start_date = models.DateTimeField()
    due_date = models.DateTimeField(null=True, blank=True)
    type = models.CharField(max_length=20, choices=TaskType.choices, default=TaskType.QUIZ)
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
        user_tasks = [
            UserTask(user=student, task=self) for student in students
        ]
        UserTask.objects.bulk_create(user_tasks)


class UserTask(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='user_tasks')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='user_tasks')
    is_completed = models.BooleanField(default=False)
    score = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('user', 'task')
        ordering = ['task__due_date']


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
    student = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    date_enrolled = models.DateTimeField(auto_now_add=True)


class Submission(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    task = models.ForeignKey(Task, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='submissions', null=True, blank=True)
    content = models.TextField(null=True, blank=True)

    def __str__(self):
        return f'Submission by {self.user.username} for {self.task.title}'

    def clean(self):
        if not self.file and not self.content:
            raise ValidationError('Either a file or content must be provided.')

