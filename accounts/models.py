from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models


class CustomUser(AbstractUser):
    profile_picture = models.ImageField(upload_to='accounts/profile_pictures', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=14, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    



    def __str__(self):
        return self.email
    
CustomUser = get_user_model()

class InstructorApplication(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    application_date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {'verified' if self.is_verified else 'not verified'} - {self.application_date}"