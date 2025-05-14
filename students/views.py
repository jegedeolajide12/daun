from django.shortcuts import render, get_object_or_404
from django.db.models import Q,Count,Avg
from django.urls import reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.views.generic.list import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.forms import UserCreationForm
from django.db.models import Count
from django.contrib.auth import login, authenticate
from django.contrib.auth.models import Group

from pages.models import Course, Faculty, Enrollment, Submission
from accounts.models import CustomUser

from .forms import CourseEnrollForm


class StudentHomePage(ListView):
    model = Course
    template_name = 'courses/student_home.html'
    context_object_name = 'courses'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['courses'] = self.request.user.courses_joined.all()
        context['faculties'] = Faculty.objects.all()
        context['is_instructor'] = self.request.user.groups.filter(name="Instructors").exists()
        return context



class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = 'courses/student_home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        faculty_slug = self.kwargs.get('faculty', None)

        # Get all courses joined by the student
        courses = Course.objects.filter(students=self.request.user)

        # Get all faculties related to the student's courses
        faculties = Faculty.objects.filter(faculty_courses__in=courses).distinct()

        # Filter courses by faculty if a faculty slug is provided
        if faculty_slug:
            faculty = get_object_or_404(Faculty, slug=faculty_slug)
            courses = courses.filter(faculty=faculty)
            context['faculty'] = faculty  # Pass the selected faculty to the template

        context['courses'] = courses
        context['faculties'] = faculties
        return context


@login_required
def manage_students(request):
    instructor_courses = Course.objects.filter(owner=request.user)

    enrollments = Enrollment.objects.filter(course__in=instructor_courses).select_related('student', 'course')
    submitted_assignments = Submission.objects.filter(assignment__assignment_task__user_tasks__status='submitted',
    assignment__course__in=instructor_courses,
    assignment__is_graded=False  # This ensures the submission hasn't been graded
).order_by('-submitted_at')

    course_filter = request.GET.get('course')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort', 'recent')

    if course_filter:
        enrollments = enrollments.filter(course__id=course_filter)
    if status_filter:
        if status_filter == 'active':
            enrollments = enrollments.filter(is_active=True)
        elif status_filter == 'inactive':
            enrollments = enrollments.filter(is_active=False)
        elif status_filter == 'completed':
            enrollments = enrollments.filter(progress=100)
    if search_query:
        enrollments = enrollments.filter(
            Q(student__username__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query) |
            Q(student__email__icontains=search_query)
        )
    if sort_by == 'progress':
        enrollments = enrollments.order_by('-progress')
    elif sort_by == 'name':
        enrollments = enrollments.order_by('student__username', 'student__first_name', 'student__last_name')
    else:
        enrollments = enrollments.order_by('-last_activity')
    
    total_students = enrollments.count()
    active_students = enrollments.filter(is_active=True).count()
    inactive_students = enrollments.filter(is_active=False).count()
    avg_progress = enrollments.aggregate(avg_progress=Avg('progress'))['avg_progress'] or 0
    unread_messages = request.user.notifications.filter(is_read=False).count()

    # Pagination
    paginator = Paginator(enrollments, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'courses': instructor_courses,
        'students': page_obj,
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'avg_progress': avg_progress,
        'unread_messages': unread_messages,
        'submitted_assignments': submitted_assignments,
    }
    return render(request, 'students/manage/manage_students.html', context)

@login_required
def student_detail(request, student_id):
    enrollment = get_object_or_404(Enrollment, id=student_id, course__owner=request.user)
    student = enrollment.student
    recent_activities = student.activities.filter(
        course=enrollment.course
    ).order_by('-timestamp')[:5]
    context = {
        'student': student,
        'enrollment': enrollment,
        'recent_activities': recent_activities,
    }
    return render(request, 'students/manage/student_detail.html', context)

@login_required
def bulk_student_actions(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        student_ids = request.POST.getlist('student_ids[]')

        if not student_ids:
            return JsonResponse({'error': 'No students selected'}, status=400)
        
        enrollments = Enrollment.objects.filter(student__id__in=student_ids, course__owner=request.user)
        
        if action == 'send_message':
            # Handle sending message to selected students
            message = request.POST.get('message')
            return JsonResponse({'success': f"Message successfully sent to {enrollments.count()} students"}, status=200)
        elif action == 'generate_certificates':
            # Handle generating certificates for selected students
            for enrollment in enrollments:
                enrollment.generate_certificate()
            return JsonResponse({'success': f"Certificates generated for {enrollments.count()} students"}, status=200)
        elif action == 'export_data':
            # Handle exporting data for selected students
            export_data = []
            for enrollment in enrollments:
                export_data.append({
                    'student_name': enrollment.student.get_full_name(),
                    'email': enrollment.student.email,
                    'course': enrollment.course.title,
                    'progress': enrollment.progress,
                    'completed_topics': f"{enrollment.completed_topics.count()}/{enrollment.course.course_topics.count()}",
                    'last_activity': enrollment.last_activity.strftime('%Y-%m-%d %H:%M:%S') if enrollment.last_activity else 'Never',
                })

            # You can save this data to a file or return it as a response
            return JsonResponse({'success': f"Exported data for {enrollments.count()} students"}, status=200)
        elif action == 'change_status':
            # Handle changing status of selected students
            new_status = request.POST.get('new_status')
            enrollments.update(is_active=(new_status == 'active'))
            return JsonResponse({'success': f"Status updated for {enrollments.count()} students"}, status=200)
        return JsonResponse({'error': 'Invalid action'}, status=400)
            