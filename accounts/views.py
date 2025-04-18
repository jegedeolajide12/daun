from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from django.contrib.auth.models import Group
from django.db.models.functions import TruncMonth
from django.db.models import Count
from django.utils.timezone import now
from django.contrib.auth import get_user_model
import calendar
import json
from datetime import timedelta, date

from .forms import InstructorApplicationForm, CustomUserChangeForm
from .models import CustomUser, InstructorApplication

from actstream.models import Action
from pages.models import Course,Task, UserTask
from allauth.account.views import SignupView

def is_admin(user):
    return user.groups.filter(name='Admin').exists()
def is_instructor(user):
    return user.groups.filter(name='Instructors').exists()


@login_required
def instructor_application(request):
    # Get or create an instructor application for the user
    application, created = InstructorApplication.objects.get_or_create(user=request.user)


    if request.method == 'POST':
        form = InstructorApplicationForm(request.POST, request.FILES, instance=application)  # ✅ Correct instance
        if form.is_valid():
            application = form.save(commit=False)

            # ✅ Update CustomUser fields from application data
            user = request.user
            user.profile_picture = form.cleaned_data.get('profile_picture')
            user.date_of_birth = form.cleaned_data.get('date_of_birth')
            user.phone_number = form.cleaned_data.get('phone_number')
            user.bio = form.cleaned_data.get('bio')

            # ✅ Save the User first
            user.save()

            

            # ✅ Mark application as pending verification
            application.is_verified = False
            application.save()

            messages.success(request, "Your application has been submitted successfully. Please wait for admin approval.")
            return redirect('student:student_home')
    else:
        form = InstructorApplicationForm(instance=application)
        # If an application already exists and is pending, prevent resubmission
    if not created and not application.is_verified:
        messages.error(request, "Your application is already submitted and is pending verification.")
        return redirect('student:student_home')
  # ✅ Correct instance

    return render(request, 'account/instructor_application.html', {'form': form})


@user_passes_test(is_admin)
def verify_application(request, application_id):
    
    try:
        application = InstructorApplication.objects.get(id=application_id)
        application.is_verified = True
        application.save()

        # Add the user to the "Instructors" group
        instructors_group, _ = Group.objects.get_or_create(name="Instructors")
        application.user.groups.add(instructors_group)


        messages.success(request, "Instructor application verified successfully.")
    except InstructorApplication.DoesNotExist:
        messages.error(request, "Instructor application not found.")

    return redirect('account:dashboard')
def reject_application(request, application_id):
    try:
        application = InstructorApplication.objects.get(id=application_id)
        application.delete()
        messages.success(request, "Instructor application rejected successfully.")
    except InstructorApplication.DoesNotExist:
        messages.error(request, "Instructor application not found.")
    return redirect('account:dashboard') 

def admin_dashboard(request):
    #admin
    # Fetch instructor applications
    applications = InstructorApplication.objects.filter(is_verified=False)
    
    # Check user roles
    is_instructor = request.user.groups.filter(name="Instructors").exists()
    is_admin = request.user.groups.filter(name="Admin").exists()
    user = get_user_model()
    actions = Action.objects.all()
    
    created_courses = Course.objects.filter(owner=request.user)
    # Count total courses
    courses_count = Course.objects.count()
    tasks = Task.objects.all()
    tasks_count = Task.objects.count()
    user_tasks = UserTask.objects.all()
    user_tasks_count = UserTask.objects.count()


    formatted_tasks = [
        {
            "title": task.title,
            "start": task.start_date.isoformat(),
            "end": task.due_date.isoformat() if task.due_date else None,
            "type": task.get_type_display(),
        }
        for task in tasks
    ]
    
    # Analytics for user registrations by the last 6 months
    six_months_ago = now() - timedelta(days=6 * 30)  # Approximation for 6 months
    user_data = (
        user.objects.filter(date_joined__gte=six_months_ago)
        .annotate(month=TruncMonth('date_joined'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    # Prepare labels and data for the last 6 months
    labels = []
    data = []
    current_date = now()

    # Generate the last 6 months dynamically
    for i in range(6):
        month_date = current_date - timedelta(days=i * 30)  # Approximation for each month
        month = month_date.month
        year = month_date.year

        # Get the user count for the specific month
        month_data = next((entry for entry in user_data if entry['month'].month == month and entry['month'].year == year), None)
        labels.insert(0, calendar.month_name[month])  # Add month name to labels
        data.insert(0, month_data['count'] if month_data else 0)  # Add count or 0 if no data

    #instructors
    
    # Context for the template
    context = {
        'created_courses': created_courses,
        'actions': actions,
        'applications': applications,
        'is_instructor': is_instructor,
        'is_admin': is_admin,
        'courses_count': courses_count,
        'tasks_count': tasks_count,
        'user_tasks_count': user_tasks_count,
        'user_task_list': user_tasks,
        'tasks': json.dumps(formatted_tasks),  # Pass tasks as JSON
        'labels': json.dumps(labels),  # Pass labels as JSON
        'data': json.dumps(data),      # Pass data as JSON
        'today': date.today()
    }

    
    return render(request, 'account/admin/dashboard.html', context)

def mail_inbox(request):
    context = {}
    return render(request, 'account/mail/mail_inbox.html', context)

def sent_mail(request):
    context = {}
    return render(request, 'account/mail/sent_mail.html', context)

def mail_draft(request):
    context = {}
    return render(request, 'account/mail/mail_draft.html', context)


def mail_compose(request):
    context = {}
    return render(request, 'account/mail/mail_compose.html', context)
