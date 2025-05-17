from django.contrib import admin
from .models import (Faculty, Course, Topic, Video, 
                     Image, Text, File, Task, 
                     UserTask, Enrollment, Notification, 
                     Assignment, Submission, SubmissionFile, Grade, 
                     Rubric, Assessment, MCQOption, AssessmentQuestion)

# Register your models here.


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}
    list_display = ['name', 'slug']
    
class TopicInline(admin.StackedInline):
    model = Topic

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug':('name',)}
    list_display = ['name', 'slug', 'created']
    list_filter = ['created', 'faculty']
    search_fields = ['name', 'overview']
    inlines = [TopicInline]

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'is_active']
    list_filter = ['is_active', 'course']
    search_fields = ['student__username', 'course__name']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['sender', 'message', 'is_read']
    list_filter = ['is_read', 'sender']
    search_fields = ['sender__username', 'message']

@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'topic', 'due_date', 'max_score']
    list_filter = ['course', 'topic', 'due_date']
    search_fields = ['title', 'course__name', 'topic__name']
    prepopulated_fields = {'slug':('title',)}

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'start_date', 'due_date']
    list_filter = ['course', 'start_date']
    search_fields = ['title', 'course__name']
    prepopulated_fields = {'slug':('title',)}


class MCQOptionInline(admin.TabularInline):
    model = MCQOption
    extra = 1
    fields = ['option_text', 'is_correct']
    list_display = ['option_text', 'is_correct']
    list_editable = ['is_correct']
    search_fields = ['option_text']

@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    inlines = [MCQOptionInline]


@admin.register(Assessment)
class AssessmentAdmin(admin.ModelAdmin):
    list_display = ['course', 'topic', 'due_date']
    list_filter = ['course', 'topic', 'due_date']
    search_fields = ['course__name', 'topic__name']



@admin.register(UserTask)
class UserTaskAdmin(admin.ModelAdmin):
    list_display = ['user', 'task', 'is_completed']
    list_filter = ['task', 'is_completed']
    list_editable = ['is_completed']
    search_fields = ['user__username', 'task__title']

admin.site.register(Video)
admin.site.register(Image)
admin.site.register(File)
admin.site.register(Text)
admin.site.register(Submission)
admin.site.register(SubmissionFile)
admin.site.register(Grade)
admin.site.register(Rubric)
