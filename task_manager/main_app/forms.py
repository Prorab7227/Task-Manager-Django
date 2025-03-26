from django import forms
from .models import *

from django.forms import DateInput
from django.contrib.auth.models import User

STATUS_CHOICE = [
    ('new', 'New'),
    ('working', 'Working'),
    ('pause', 'Pause'),
    ('done', 'Done'),
    ('closed', 'Closed'),
    ('archive', 'Archive'),
]

PRIORITY_CHOICE = [
    ('low', 'Low'),
    ('regular', 'Regular'),
    ('high', 'High'),
]

def get_default_folder():
    return Folder.objects.filter(name="General").first()

def get_default_tag():
    return Tag.objects.filter(name="General").first()

class FolderForm(forms.ModelForm):
    parent_folder = forms.ModelChoiceField(
        queryset=Folder.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn'}),
        empty_label="-",
    )

    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(
            attrs={'class': 'form-control multiselect', 'multiple': 'multiple'}
        )
    )
    
    assignee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn'}),
        empty_label="-"
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICE,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn', 'data-width': '150'}),
        initial='new'
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICE,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn', 'data-width': '150'}),
        initial='regular'
    )

    class Meta:
        model = Folder
        fields = ['name', 'description', 'client', 'status', 'members', 'priority', 'assignee', 'parent_folder']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter folder name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter description...', 'id': 'ckeditor_classic_empty'}),
            'client': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client name'}),
        }
        labels = {
            'name': 'Folder Name',
            'description': 'Description',
            'client': 'Client',
            'status': 'Status',
            'members': 'Members',
            'priority': 'Priority',
            'assignee': 'Assignee',
            'parent_folder': 'Parent folder'
        }


class ProjectForm(forms.ModelForm):
    folder = forms.ModelChoiceField(
        queryset=Folder.objects.filter(parent_folder__isnull=True),
        required=False,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn'}),
        empty_label="-",
        initial=get_default_folder
    )

    subfolder = forms.ModelChoiceField(
        queryset=Folder.objects.filter(parent_folder__isnull=False),
        required=False,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn'}),
        empty_label="-",
    )

    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'multiselect dropdown-toggle btn'}),
    )

    assignee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn'}),
        empty_label="-"
    )

    deadline = forms.DateField(
        widget=DateInput(format='%d.%m.%Y', attrs={'class': 'form-control', 'id': 'mask_date', 'placeholder': 'Enter deadline date'}),
        input_formats=['%d.%m.%Y'],
        required=False
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICE,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn', 'data-width': '150'}),
        initial='new'
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICE,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn', 'data-width': '150'}),
        initial='regular'
    )

    tag = forms.ModelChoiceField(
        queryset=Tag.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn'}),
        empty_label="-",
    )


    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter description...',
            'id': 'ckeditor_classic_empty',
        }),
        required=False
    )

    class Meta:
        model = Project
        fields = ['name', 'description', 'tag', 'client', 'members', 'assignee', 'deadline', 'status', 'priority', 'folder', 'subfolder']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter name of project'}),
            'client': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter client name'}),
        }
        labels = {
            'name': 'Project Name',
            'tag': 'Project Tag',
            'description': 'Description',
            'client': 'Client',
            'members': 'Members',
            'assignee': 'assignee',
            'deadline': 'Deadline',
            'status': 'Status',
            'priority': 'Priority',
            'folder': 'Folder',
            'subfolder': 'Subfolder'
        }


class TaskForm(forms.ModelForm):
    members = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control multiselect', 'multiple': 'multiple'})
    )

    assignee = forms.ModelChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn'}),
        empty_label="-"
    )

    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=False,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn', 'data-width': '150'}),
        empty_label="-",
    )

    deadline = forms.DateField(
        widget=DateInput(format='%d.%m.%Y', attrs={'class': 'form-control', 'id': 'mask_date', 'placeholder': 'Enter deadline date'}),
        input_formats=['%d.%m.%Y'],
        required=False
    )

    status = forms.ChoiceField(
        choices=STATUS_CHOICE,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn', 'data-width': '150'}),
        initial='new'
    )

    priority = forms.ChoiceField(
        choices=PRIORITY_CHOICE,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn', 'data-width': '150'}),
        initial='regular'
    )

    class Meta:
        model = Task
        fields = ['title', 'description', 'deadline', 'status', 'priority', 'members', 'project', 'assignee']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter task name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter description...', 'id': 'ckeditor_classic_empty'}),
        }

        labels = {
            'title': 'Title',
            'description': 'Description',
            'deadline': 'Deadline',
            'status': 'Status',
            'priority': 'Priority',
            'members': 'Members',
            'project': 'Project',
            'assignee': 'Assignee',
        }


class TaskCommentForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter comment text...',
            'id': 'ckeditor_classic_empty',
        })
    )
    
    class Meta:
        model = TaskComment
        fields = ['text']

        labels = {
            'text': 'Text',
        }

class ProjectCommentForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Enter comment text...',
            'id': 'ckeditor_classic_empty',
        })
    )
    
    class Meta:
        model = ProjectComment
        fields = ['text']

        labels = {
            'text': 'Text',
        }



class TaskFileForm(forms.ModelForm):
    class Meta:
        model = TaskFile
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        files = self.files.getlist('file')
        # for file in files:
        #     if file.size > 100 * 1024 * 1024:  # Ограничение размера
        #         raise forms.ValidationError(f"The file {file.name} exceeds the allowed size of 100 MB.")
        return cleaned_data

class ProjectReportForm(forms.ModelForm):
    text = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Enter text...', 'id': 'ckeditor_classic_empty'}),
        label='Report Text'
    )
    link = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'Enter URL...', 'id': 'link_input'}),
        label='Report Link'
    )
    project = forms.ModelChoiceField(
        queryset=Project.objects.all(),
        required=True,
        widget=forms.Select(attrs={'class': 'multiselect dropdown-toggle btn', 'data-width': '150'}),
        empty_label="-",
    )

    class Meta:
        model = ProjectReport
        fields = ['text', 'link', 'project']

class ProjectReportFileForm(forms.ModelForm):
    class Meta:
        model = ProjectReportFile
        fields = []

    def clean(self):
        cleaned_data = super().clean()
        files = self.files.getlist('file')
        # for file in files:
        #     if file.size > 100 * 1024 * 1024:  # Ограничение размера
        #         raise forms.ValidationError(f"The file {file.name} exceeds the allowed size of 100 MB.")
        return cleaned_data

class TagFrom(forms.ModelForm):
    class Meta:
        model = Tag
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter name of tag'}),
        }
        labels = {
            'name': 'Tag Name'
        }

class LoginForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput())
    password = forms.CharField(widget=forms.PasswordInput())

class SignupForm(forms.Form):
    username = forms.CharField(max_length=100, widget=forms.TextInput())
    password1 = forms.CharField(widget=forms.PasswordInput())
    password2 = forms.CharField(widget=forms.PasswordInput())
    email = forms.EmailField(widget=forms.EmailInput())