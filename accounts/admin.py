from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group

from .models import CustomUser,InstructorApplication, InstructorRating
from .forms import InstructorApplicationForm, CustomUserChangeForm


class InstructorAdmin(UserAdmin):
    add_form = InstructorApplicationForm
    form = CustomUserChangeForm
    model = CustomUser

    list_display = ('username', 'email', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_active')

    fieldsets = (
        (None, {'fields': ('username', 'email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name', 'profile_picture', 'date_of_birth', 'bio', 'phone_number')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'groups', 'user_permissions')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active')}
        ),
    )

    search_fields = ('username', 'email')
    ordering = ('username',)

admin.site.register(CustomUser, InstructorAdmin)

@admin.register(InstructorRating)
class InstructorRatingAdmin(admin.ModelAdmin):
    list_display = ('instructor', 'student', 'rating', 'comment', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('instructor__username', 'user__username', 'comment')
    ordering = ('-created_at',)

    def instructor(self, obj):
        return obj.instructor.username
    instructor.short_description = 'Instructor'


@admin.register(InstructorApplication)
class InstructorApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'application_date', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('user__username', 'user__email')
    ordering = ('-application_date',)
    actions = ['approve_applications', 'reject_applications']
    def approve_applications(self, request, queryset):
        instructors_group, _ = Group.objects.get_or_create(name='Instructors')
        for application in queryset:
            application.is_verified = True
            application.user.groups.add(instructors_group)
            application.user.save()
            application.save()
    approve_applications.short_description = "Approve selected instructor applications"
    def reject_applications(self, request, queryset):
        for application in queryset:
            application.is_verified = False
            application.save()
    reject_applications.short_description = "Reject selected instructor applications"