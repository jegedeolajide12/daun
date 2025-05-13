from django import forms

from django.core.exceptions import ValidationError
from django.forms.models import inlineformset_factory

from .models import Course, Topic, Faculty, Assignment, Submission

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
                'id': 'id_title',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter Assignment Description',
                'id': 'id_description',
            }),
            'course': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select Course',
                'id': 'id_course',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
                'placeholder': 'Select Due Date',
                'id': 'id_due_date',
            }),
            'topic': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select Topic',
                'id': 'id_topic',
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
            }),
            'max_score': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': 'Enter Max Score',
                'id': 'id_max_score',
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



class SubmissionForm(forms.ModelForm):
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 8,
            'placeholder': 'Write your solution here...'
        }),
        required=True
    )
    files = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'accept': '.pdf,.doc,.docx,.jpg,.jpeg,.png,.txt,.py,.zip'
        }),
        required=False
    )

    class Meta:
        model = Submission
        fields = ['files', 'content']

    def clean_file(self):
        files = self.files.getlist('file')
        if len(files) > 5:
            raise ValidationError("You can upload a maximum of 5 files.")
        
        for file in files:
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise ValidationError(f"File {file.name} exceeds 10MB size limit.")
            
            # Validate file extensions
            valid_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.txt', '.py', '.zip']
            if not any(file.name.lower().endswith(ext) for ext in valid_extensions):
                raise ValidationError(f"Invalid file type for {file.name}. Allowed types: PDF, DOC, images, text, Python, ZIP")
        
        return files