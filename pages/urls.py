from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (index, 
                    ManageCourseListView, 
                    CourseCreateView, 
                    CourseUpdateView, 
                    CourseDeleteView, 
                    course_detail,
                    CourseModuleUpdateView,
                    ContentCreateUpdateView,
                    topic_detail,
                    ContentDeleteView)


app_name = 'course'

urlpatterns = [
    path('', index, name='index'),
    path('home/', ManageCourseListView.as_view(), name='home'),
    path('course/<slug:course_slug>/', course_detail, name='course'),
    path('course/create/', CourseCreateView.as_view(), name='course_create'),
    path('courses/<slug:slug>/edit/', CourseUpdateView.as_view(), name='course_update'),
    path('courses/<slug:slug>/delete/',CourseDeleteView.as_view(), name='course_delete'),
    path('<slug:course_slug>/topic/manage', CourseModuleUpdateView.as_view(), name='course_module_update'),
    path('topic/<int:topic_id>/content/<str:model_name>/create/', ContentCreateUpdateView.as_view(), name='topic_content_create'),
    path('topic/<int:topic_id>/content/<model_name>/<id>/', ContentCreateUpdateView.as_view(), name='topic_content_update'),
    path('topic/<int:topic_id>/view/', topic_detail, name='topic_detail'),
    path('content/<int:content_id>/delete', ContentDeleteView.as_view(), name='content_delete'),
    
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
