from django import forms
from .models import Submission, Evaluation, Announcement, ChatMessage

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['title', 'description', 'document']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
        }

class ReviewForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('mentor_approved', 'Approve'),
        ('mentor_rejected', 'Reject'),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Submission
        fields = ['mentor_feedback', 'status']
        widgets = {
            'mentor_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class EvaluationForm(forms.ModelForm):
    quality = forms.IntegerField(min_value=0, max_value=10)
    methodology = forms.IntegerField(min_value=0, max_value=10)
    presentation = forms.IntegerField(min_value=0, max_value=10)
    comments = forms.CharField(widget=forms.Textarea, required=False)

    class Meta:
        model = Evaluation
        fields = ['quality', 'methodology', 'presentation', 'comments']

class ApprovalForm(forms.ModelForm):
    STATUS_CHOICES = [
        ('coordinator_approved', 'Approve'),
        ('mentor_rejected', 'Reject'),
    ]
    status = forms.ChoiceField(choices=STATUS_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))

    class Meta:
        model = Submission
        fields = ['coordinator_feedback', 'status']
        widgets = {
            'coordinator_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ChatMessageForm(forms.ModelForm):
    class Meta:
        model = ChatMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

class LoginForm(forms.Form):
    user_id = forms.CharField(
        label="User ID (Student ID, Mentor ID, or Coordinator ID)",
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your ID'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'})
    )

class StudentUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload Student CSV (section, batch id, name, roll no, mentor allotted, coordinator allotted, gmailid)")

class MentorUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload Mentor CSV (mentor id, name, gmailid)")

class CoordinatorUploadForm(forms.Form):
    csv_file = forms.FileField(label="Upload Coordinator CSV (coordinator id, name, gmailid)")