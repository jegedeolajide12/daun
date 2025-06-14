from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

from .views import (index, ManageCourseListView, CourseCreateView, CourseUpdateView, CourseDeleteView, 
                    course_detail, CourseModuleUpdateView, ContentCreateUpdateView, topic_detail, 
                    ContentDeleteView, CourseListView, course_unenroll, create_faculty, get_notifications, 
                    mark_notification_read, mark_all_notifications_read, create_assignment,
                    submit_assignment, assignment_detail, grade_assignments, get_submission_details, 
                    grade_submissions, create_assessment, manage_courses, attempt_assessment,
                    assessment_result, CourseCreateWizard, course_enroll)


app_name = 'course'

urlpatterns = [
    path('', index, name='index'),
    path('courses/', CourseListView.as_view(), name='course_list'),
    path('coures/manage/', manage_courses, name='manage_courses'),

    path('faculty/create/', create_faculty, name='create_faculty'),
    path('home/', ManageCourseListView.as_view(), name='home'),
    path('course/create/', CourseCreateWizard.as_view(), name='course_create'),
    path('course/<slug:course_slug>/', course_detail, name='course'),
    path('courses/<slug:slug>/edit/', CourseUpdateView.as_view(), name='course_update'),
    path('courses/<slug:slug>/delete/',CourseDeleteView.as_view(), name='course_delete'),
    path('<slug:course_slug>/topic/manage', CourseModuleUpdateView.as_view(), name='course_module_update'),
    path('topic/<int:topic_id>/content/<str:model_name>/create/', ContentCreateUpdateView.as_view(), name='topic_content_create'),
    path('topic/<int:topic_id>/content/<model_name>/<id>/', ContentCreateUpdateView.as_view(), name='topic_content_update'),
    path('topic/<int:topic_id>/view/', topic_detail, name='topic_detail'),
    path('content/<int:content_id>/delete', ContentDeleteView.as_view(), name='content_delete'),
    
    path('course/<slug:course_slug>/enroll/', course_enroll, name="enroll_course"),
    path('courses/<slug:course_slug>/unenroll/', course_unenroll, name='course_unenroll'),


    path('notifications/', get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/mark-read', mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_read'),

    path('course/<int:course_id>/assignment/create/', create_assignment, name='create_assignment'),
    path('course/<int:course_id>/topic/<int:topic_id>/assignment/<int:assignment_id>/submit', submit_assignment, name='submit_assignment'),
    path('assignment/<int:assignment_id>/topic/<int:topic_id>/course/<int:course_id>/detail', assignment_detail, name='assignment_detail'),
    path('students/assignments/grade', grade_assignments, name='grade_assignments'),
    path('course/students/assignments/<int:submission_id>/detail', get_submission_details, name='get_submission_details'),
    path('course/students/assignments/<int:submission_id>/grade', grade_submissions, name='grade_submissions'),

    path('course/<int:course_id>/assessment/create', create_assessment, name='create_assessment'),
    path('assessment/<int:assessment_id>/attempt/', attempt_assessment, name='attempt_assessment'),
    path('assessment/<int:attempt_id>/result/', assessment_result, name='assessment_result'),
]
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
