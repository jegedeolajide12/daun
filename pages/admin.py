from django.contrib import admin
from .models import Faculty, Course, Topic, Video, Image, Text, File

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
    search_fields = ['title', 'overview']
    inlines = [TopicInline]

admin.site.register(Video)
admin.site.register(Image)
admin.site.register(File)
admin.site.register(Text)

