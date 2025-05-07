from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.contrib.auth.models import Group



from .models import CustomUser, InstructorRating


class CustomUserChangeForm(UserChangeForm):
    password = None

    class Meta:
        model = CustomUser
        fields = ['email', 'username', 'first_name', 'last_name', 
              'address', 'bio', 'city', 'company', 
              'country', 'date_of_birth', 'github', 'instagram', 
              'linkedin', 'occupation', 'phone_number', 'postal_code', 
              'profile_picture', 'state', 'twitter']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'rows':4,'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'rows':4, 'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'company': forms.TextInput(attrs={'class': 'form-control'}),
            'country': forms.TextInput(attrs={'class': 'form-control'}),
            'github': forms.TextInput(attrs={'class': 'form-control'}),
            'instagram': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin': forms.TextInput(attrs={'class': 'form-control'}),
            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'postal_code': forms.TextInput(attrs={'class': 'form-control'}),
            'profile_picture': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'state': forms.TextInput(attrs={'class': 'form-control'}),
            'twitter': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'date_of_birth': 'Date of Birth',
            'postal_code': 'Zip/Postal Code',
            'profile_picture': 'Profile Picture',
        }



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

class InstructorRatingForm(forms.ModelForm):
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