from django.contrib import admin
from .models import (Faculty, 
                     Course, 
                     Topic, 
                     Video, 
                     Image, 
                     Text, 
                     File, 
                     Task,
                     UserTask)

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

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'course', 'start_date', 'due_date']
    list_filter = ['course', 'start_date']
    search_fields = ['title', 'course__name']
    prepopulated_fields = {'slug':('title',)}

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

