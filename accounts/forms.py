from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group



from .models import CustomUser, InstructorRating

    


class InstructorApplicationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['profile_picture', 'date_of_birth', 'phone_number', 'bio']
        widgets = {
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control'}),
        }

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ('email', 'username',)


class RatingForm(forms.ModelForm):
    class Meta:
        model = InstructorRating
        fields = ['rating', 'comment']
        widgets = {
            'rating': forms.NumberInput(attrs={
                'type': 'range',
                'min': '1',
                'max': '5',
                'step': '1',
                'class': 'form-range'
            }),
            'comment': forms.Textarea(attrs={
                'rows': 3,
                'class': 'form-control',
                'placeholder': 'Optional feedback...'
            })
        }