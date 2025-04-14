from django.db import models
import hashlib
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User

class Section(models.Model):
    SECTIONS = [
        ('A', 'A Section'), ('B', 'B Section'), ('C', 'C Section'),
        ('D', 'D Section'), ('E', 'E Section'),
    ]
    section_id = models.CharField(max_length=1, choices=SECTIONS, primary_key=True)

    def __str__(self):
        return self.section_id

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    student_id = models.CharField(max_length=20, primary_key=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    team = models.ForeignKey('Team', on_delete=models.CASCADE, null=True, blank=True)  # Single team field, nullable
    section = models.ForeignKey(Section, on_delete=models.CASCADE)
    password = models.CharField(max_length=128, default=make_password("Gradify2025"))
    user_type = models.CharField(max_length=10, default='student')
    contact_no = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.name

class Team(models.Model):
    team_id = models.CharField(max_length=20, primary_key=True)
    mentor = models.ForeignKey('Mentor', on_delete=models.CASCADE)
    section = models.ForeignKey(Section, on_delete=models.CASCADE)

    def __str__(self):
        return self.team_id

class Mentor(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    mentor_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    coordinator = models.ForeignKey('Coordinator', on_delete=models.CASCADE)
    password = models.CharField(max_length=128, default=make_password("Gradify2025"))
    user_type = models.CharField(max_length=10, default='mentor')
    contact_no = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.name

class Coordinator(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True)
    coordinator_id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=128, default=make_password("Gradify2025"))
    user_type = models.CharField(max_length=20, default='coordinator')
    contact_no = models.CharField(max_length=15, blank=True, null=True)

    def __str__(self):
        return self.name

class Submission(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('mentor_approved', 'Mentor Approved'),
        ('mentor_rejected', 'Mentor Rejected'),
        ('coordinator_approved', 'Coordinator Approved'),
    ]
    submission_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    document = models.FileField(upload_to='submissions/')
    document_hash = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_at = models.DateTimeField(auto_now_add=True)
    mentor_feedback = models.TextField(blank=True, null=True)
    coordinator_feedback = models.TextField(blank=True, null=True)
    mentor_signature = models.CharField(max_length=256, blank=True, null=True)
    coordinator_signature = models.CharField(max_length=256, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.document and not self.document_hash:
            file_content = self.document.read()
            self.document_hash = hashlib.sha256(file_content).hexdigest()
            self.document.seek(0)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class Evaluation(models.Model):
    submission = models.ForeignKey(Submission, on_delete=models.CASCADE)  # Changed from OneToOneField
    quality = models.IntegerField()
    methodology = models.IntegerField()
    presentation = models.IntegerField()
    total_score = models.DecimalField(max_digits=5, decimal_places=2)
    comments = models.TextField(blank=True, null=True)
    evaluated_by_mentor = models.ForeignKey(Mentor, on_delete=models.CASCADE, null=True, blank=True)
    evaluated_by_coordinator = models.ForeignKey(Coordinator, on_delete=models.CASCADE, null=True, blank=True)

    def save(self, *args, **kwargs):
        quality = self.quality if self.quality is not None else 0
        methodology = self.methodology if self.methodology is not None else 0
        presentation = self.presentation if self.presentation is not None else 0
        self.total_score = (quality * 0.4 + methodology * 0.3 + presentation * 0.3) * 10
        super().save(*args, **kwargs)

    class Meta:
        unique_together = [['submission', 'evaluated_by_mentor'], ['submission', 'evaluated_by_coordinator']]  # One eval per evaluator per submission

    def __str__(self):
        evaluator = self.evaluated_by_mentor or self.evaluated_by_coordinator
        return f"Evaluation of {self.submission.title} by {evaluator}"

class Announcement(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.CharField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.title

class ChatMessage(models.Model):
    sender_student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.CASCADE)
    sender_mentor = models.ForeignKey(Mentor, null=True, blank=True, on_delete=models.CASCADE)
    recipient_student = models.ForeignKey(Student, null=True, blank=True, on_delete=models.CASCADE, related_name='received_messages')
    recipient_mentor = models.ForeignKey(Mentor, null=True, blank=True, on_delete=models.CASCADE, related_name='received_messages')
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender_student or self.sender_mentor} at {self.timestamp}"