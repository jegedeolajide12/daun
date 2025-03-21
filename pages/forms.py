from django import forms

from django.forms.models import inlineformset_factory

from .models import Course, Topic

ModuleFormSet = inlineformset_factory(Course, Topic, fields=['name', 'description'], extra=2, can_delete=True)


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['faculty', 'name', 'overview', 'cover_image', 'code']
        widgets = {
            'faculty': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Faculty Name',
            }),
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'value': 'Mark Andre',
                'placeholder': 'Enter Course Name',
            }),
            'overview': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter Course Overview',
            }),
            'cover_image': forms.FileInput(attrs={
                'class': 'form-control',
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Course Code',
            }),
        }
