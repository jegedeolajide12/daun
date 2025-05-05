from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Avg


class CustomUser(AbstractUser):
    profile_picture = models.ImageField(upload_to='accounts/profile_pictures', null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=14, null=True, blank=True)
    bio = models.TextField(blank=True, null=True)
    
    @property
    def average_rating(self):
        ratings = self.ratings_recieved.aggregate(Avg('rating'))
        return ratings['rating__avg'] if ratings['rating__avg'] else 0
    
    @property
    def total_ratings(self):
        return self.ratings_recieved.count()
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}" if self.first_name and self.last_name else self.username

    

    def __str__(self):
        return self.email
    
CustomUser = get_user_model()


class InstructorRating(models.Model):
    instructor = models.ForeignKey(CustomUser, 
                                   on_delete=models.CASCADE, 
                                   related_name='ratings_recieved',
                                   limit_choices_to={'is_staff': True})
    student = models.ForeignKey(CustomUser, 
                                on_delete=models.CASCADE, 
                                related_name='ratings_given')
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rate the instructor from 1 to 5"
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('instructor', 'student')
        verbose_name = 'Instructor Rating'
        verbose_name_plural = 'Instructor Ratings'
    
    def __str__(self):
        return f"{self.username} rated {self.instructor.username} - {self.rating}/5"



class InstructorApplication(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    application_date = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {'verified' if self.is_verified else 'not verified'} - {self.application_date}"

