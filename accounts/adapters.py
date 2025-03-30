from allauth.account.adapter import DefaultAccountAdapter

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        user = super().save_user(request, user, form, commit=False)

        # Get role from request URL (default to 'student' if not provided)
        role = request.GET.get("role", "student")
        if role in ["student", "teacher"]:  # Ensure only valid roles are assigned
            user.role = role
        
        if commit:
            user.save()
        return user
