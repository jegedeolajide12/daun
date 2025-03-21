from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    profile_picture = models.ImageField(upload_to='accounts/profile_pictures', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=14, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.email