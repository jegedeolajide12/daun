from cProfile import label
from django import forms

from django.core.exceptions import ValidationError
from django.contrib.contenttypes.models import ContentType
from pkg_resources import require

from .models import (Course, Topic, Faculty, Assignment, 
                     Submission, Assessment, MCQOption, AssessmentQuestion, 
                     Content, Text, File, Image, Video,
                     CourseTrailer, CourseRequirements, CourseObjectives)




class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'overview', 'cover_image', 'code', 'audience']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
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
            'audience': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select Audience',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['overview'].required = False


class CourseObjectivesForm(forms.ModelForm):
    class Meta:
        model = CourseObjectives
        fields = ['objective']
        widgets = {
            'objective': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter Course Objective',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['objective'].required = True


class CourseBasicsForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['faculty', 'name', 'overview', 'cover_image', 'code', 'audience']
        widgets = {
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
            'audience': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select Audience',
            }),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['faculty'].queryset = Faculty.objects.all()
        self.fields['faculty'].widget.attrs.update({'class': 'form-control'})

class CourseTopicsForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Topic Name',
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter Topic Description',
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['name'].required = True
        self.fields['description'].required = False

CONTENT_MODELS = {
    'text': Text,
    'file': File,
    'image': Image,
    'video': Video,
}
class CourseTopicContentsForm(forms.ModelForm):
    class Meta:
        model = Content
        fields = ['topic', 'content_type', 'order']
        
    content_type = forms.ModelChoiceField(
        queryset=ContentType.objects.filter(model__in=CONTENT_MODELS.keys()),
        widget=forms.Select(attrs={
            'class': 'form-control',
            'placeholder': 'Select Content Type',
        }),
        label='Content Type',
    ),
    text_content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Enter Text Content',
        }),
        label='Text Content',
        required=False,
    ),
    file_content = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'placeholder': 'Upload File Content',
        }),
        label='File Content',
        required=False,
    ),
    image_content = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'placeholder': 'Upload Image Content',
        }),
        label='Image Content',
        required=False,
    ),
    video_file = forms.FileField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
            'placeholder': 'Upload Video Content',
        }),
        label='Video File',
        required=False,
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['topic'].queryset = Topic.objects.all()
        self.fields['topic'].widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        ctype = cleaned_data.get('content_type')
        if not ctype:
            raise forms.ValidationError("Please select a content type.")

        model = ctype.model
        # Validate and create the related item
        if model == 'text':
            content = cleaned_data.get('text_content')
            if not content:
                self.add_error('text_content', "Text content is required.")
        elif model == 'file':
            file = cleaned_data.get('file_content')
            if not file:
                self.add_error('file_content', "File is required.")
        elif model == 'image':
            image = cleaned_data.get('image_content')
            if not image:
                self.add_error('image_content', "Image is required.")
        elif model == 'video':
            file = cleaned_data.get('video_file')
            if not file:
                self.add_error('video_file', "Provide a video URL or upload a file.")
        return cleaned_data

    def save(self, commit=True, owner=None):
        # Create the related item instance
        ctype = self.cleaned_data['content_type']
        model = ctype.model
        item = None

        if model == 'text':
            item = Text.objects.create(
                owner=owner,
                title="Text Content",
                content=self.cleaned_data['text_content']
            )
        elif model == 'file':
            item = File.objects.create(
                owner=owner,
                title="File Content",
                file=self.cleaned_data['file_content']
            )
        elif model == 'image':
            item = Image.objects.create(
                owner=owner,
                title="Image Content",
                file=self.cleaned_data['image_content']
            )
        elif model == 'video':
            item = Video.objects.create(
                owner=owner,
                title="Video Content",
                url=self.cleaned_data['video_url'],
                file=self.cleaned_data['video_file']
            )

        # Save the Content instance
        content = super().save(commit=False)
        content.content_type = ctype
        content.object_id = item.id
        if commit:
            content.save()
        return content

class CourseTopicAssignmentsForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['title', 'description', 'topic', 'file', 'max_score']
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
        super().__init__(*args, **kwargs)

        if self.instance and hasattr(self.instance, 'course') and self.instance.course:
            self.fields['topic'].queryset = Topic.objects.filter(course=self.instance.course)
        else:
            self.fields['topic'].queryset = Topic.objects.none()
        
        self.fields['file'].required = False
        self.fields['topic'].empty_label = "Select Topic"


class CourseTopicAssessmentsForm(forms.ModelForm):
    class Meta:
        model = Assessment
        fields = ['points', 'time_limit', 'topic']
        widgets = {
            'points': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'placeholder': 'Enter Points',
            }),
            'time_limit': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'placeholder': 'Enter Time Limit (in minutes)',
            }),
            'topic': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select Topic',
                'id': 'id_topic',
            }),
        }
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        if user and user.is_authenticated:
            self.fields['topic'].queryset = Topic.objects.filter(course__owner=user)
        else:
            self.fields['topic'].queryset = Topic.objects.none()
        
        self.fields['topic'].empty_label = "Select Topic"
    
    def clean(self):
        points = self.cleaned_data.get('points')
        if points is not None and points < 0:
            raise ValidationError("Points cannot be negative.")
        return self.cleaned_data
    
    def clean_time_limit(self):
        time_limit = self.cleaned_data.get('time_limit')
        if time_limit is not None and time_limit < 1:
            raise ValidationError("Time limit must be at least 1 minute.")
        return time_limit

class AssessmentQuestionForm(forms.ModelForm):
    class Meta:
        model = AssessmentQuestion
        fields = ['question', 'explanation']
        widgets = {
            'question': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter Question',
            }),
            'explanation': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter Explanation',
            }),
        }
    
class MCQOptionForm(forms.ModelForm):
    class Meta:
        model = MCQOption
        fields = ['option_text', 'is_correct']
        widgets = {
            'option_text': forms.TextInput(attrs={
                'class': 'form-control option-text',
                'placeholder': 'Enter Option Text',
            }),
            'is_correct': forms.CheckboxInput(attrs={
                'class': 'form-check-input is-correct-checkbox',
            }),
        }

class CourseTrailerForm(forms.ModelForm):
    class Meta:
        model = CourseTrailer
        fields = ['video_url', 'file']
        widgets = {
            'video_url': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Video URL',
            }),
            'file': forms.ClearableFileInput(attrs={
                'class': 'form-control',
                'placeholder': 'Upload Video File',
            }),
        }
class CourseRequirementsForm(forms.ModelForm):
    class Meta:
        model = CourseRequirements
        fields = ['requirement']
        widgets = {
            'requirement': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter Course Requirements',
            }),
        }

class CourseMarketingForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['price_tier', 'is_active', 'is_featured']
        widgets = {
            'price_tier': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select Price Tier',
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'is_featured': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
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


