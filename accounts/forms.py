from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    profile_picture = forms.ImageField(required=False, label="Profile Picture")
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type':'date'}), label="Date of Birth")
    bio = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows':4}), label="Short bio")
    phone_number = forms.CharField(required=False,max_length=14, label="Phone number", widget=forms.TextInput(attrs={'placeholder':'+2341234567891'}))
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('email', 'username', 'profile_picture', 'date_of_birth', 'bio', 'phone_number')

class CustomUserChangeForm(UserChangeForm):

    class Meta:
        model = CustomUser
        fields = ('email', 'username',)