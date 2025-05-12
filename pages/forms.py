from django import forms

from django.forms.models import inlineformset_factory

from .models import Course, Topic, Faculty, Assignment

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

class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = ['name']
        widgets = {
            'name': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Faculty Name',
            }),
        }

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description','due_date', 'course', 'topic', 'file', 'max_score']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Assignment Name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter Assignment Description',
            }),
            'course': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select Course',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Select Due Date',
            }),
            'topic': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select Topic',
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': 'Enter Max Score',
            }),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(AssignmentForm, self).__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields['course'].queryset = Course.objects.filter(owner=user)

        if self.instance and hasattr(self.instance, 'course') and self.instance.course:
            self.fields['topic'].queryset = Topic.objects.filter(course=self.instance.course)
        else:
            self.fields['topic'].queryset = Topic.objects.none()
        
        self.fields['file'].required = False
        self.fields['topic'].empty_label = "Select Topic"