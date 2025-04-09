from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required,user_passes_test
from django.contrib import messages
from django.contrib.auth.models import Group

from .forms import InstructorApplicationForm, CustomUserChangeForm
from .models import CustomUser, InstructorApplication


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

@user_passes_test(lambda user: is_instructor(user) or is_admin(user))
def admin_dashboard(request):
    applications = InstructorApplication.objects.filter(is_verified=False)
    context = {'applications': applications}
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
