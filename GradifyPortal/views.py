from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
import hashlib
import os
from .models import Student, Submission, Team, Mentor, Coordinator, Evaluation, Announcement, ChatMessage, Section
from .forms import SubmissionForm, ReviewForm, EvaluationForm, ApprovalForm, AnnouncementForm, ChatMessageForm, LoginForm
from django.conf import settings
from django.contrib.auth.hashers import check_password
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import HttpResponseForbidden, HttpResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse

def debug_auth(request):
    return HttpResponse(f"Authenticated: {request.user.is_authenticated}, User: {request.user.username}")

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user_id = form.cleaned_data['user_id']
            password = form.cleaned_data['password']

            # Try to authenticate based on user_id and password
            user = None
            try:
                student = Student.objects.get(student_id=user_id)
                user = authenticate(request, username=user_id, password=password)
                if user and hasattr(student, 'user') and student.user == user:
                    login(request, user)
                    request.session['user_id'] = user_id
                    request.session['user_type'] = 'student'
                    return redirect('GradifyPortal:student_dashboard', student_id=user_id)
            except Student.DoesNotExist:
                pass
            
            try:
                mentor = Mentor.objects.get(mentor_id=user_id)
                user = authenticate(request, username=str(user_id), password=password)
                if user and hasattr(mentor, 'user') and mentor.user == user:
                    login(request, user)
                    request.session['user_id'] = user_id
                    request.session['user_type'] = 'mentor'
                    return redirect('GradifyPortal:mentor_dashboard', mentor_id=user_id)
            except Mentor.DoesNotExist:
                pass
            
            try:
                coordinator = Coordinator.objects.get(coordinator_id=user_id)
                user = authenticate(request, username=str(user_id), password=password)
                if user and hasattr(coordinator, 'user') and coordinator.user == user:
                    login(request, user)
                    request.session['user_id'] = user_id
                    request.session['user_type'] = 'coordinator'
                    return redirect('GradifyPortal:coordinator_dashboard', coordinator_id=user_id)
            except Coordinator.DoesNotExist:
                pass
            
            messages.error(request, 'Invalid ID or password.')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    logout(request)  # Use Django's logout to clear auth session
    request.session.flush()  # Clear all session data
    messages.success(request, "You have been logged out successfully.")
    return redirect('GradifyPortal:login')  # Redirect to login page

# Student Views
def student_dashboard(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    team = student.team
    submissions = Submission.objects.filter(team=team)
    
    # Add status_with_emoji to each submission
    for submission in submissions:
        if submission.status == "pending":
            submission.status_with_emoji = f"{submission.get_status_display()} ⏳"
        elif submission.status in ("mentor_rejected", "coordinator_rejected"):
            submission.status_with_emoji = f'{submission.get_status_display()} <span style="color: red;">❌</span>'
        elif submission.status in ("mentor_approved", "coordinator_approved"):
            submission.status_with_emoji = f'{submission.get_status_display()} <span style="color: green;">✅</span>'
        else:
            submission.status_with_emoji = submission.get_status_display()

    announcements = Announcement.objects.all().order_by('-created_at')[:3]  # Show latest 3
    evaluations = Evaluation.objects.filter(submission__team=team)
    unread_messages = ChatMessage.objects.filter(recipient_student=student, is_read=False).count()
    
    # Calculate average scores for each submission with evaluations
    submission_evaluations = {}
    for submission in submissions:
        mentor_eval = Evaluation.objects.filter(submission=submission, evaluated_by_mentor__isnull=False).first()
        coordinator_eval = Evaluation.objects.filter(submission=submission, evaluated_by_coordinator__isnull=False).first()
        
        if mentor_eval or coordinator_eval:
            # Average quality scores
            mentor_quality = mentor_eval.quality if mentor_eval else 0
            coordinator_quality = coordinator_eval.quality if coordinator_eval else 0
            avg_quality = (mentor_quality + coordinator_quality) / 2 if (mentor_eval and coordinator_eval) else (mentor_quality or coordinator_quality)
            
            # Average methodology scores
            mentor_methodology = mentor_eval.methodology if mentor_eval else 0
            coordinator_methodology = coordinator_eval.methodology if coordinator_eval else 0
            avg_methodology = (mentor_methodology + coordinator_methodology) / 2 if (mentor_eval and coordinator_eval) else (mentor_methodology or coordinator_methodology)
            
            # Average presentation scores
            mentor_presentation = mentor_eval.presentation if mentor_eval else 0
            coordinator_presentation = coordinator_eval.presentation if coordinator_eval else 0
            avg_presentation = (mentor_presentation + coordinator_presentation) / 2 if (mentor_eval and coordinator_eval) else (mentor_presentation or coordinator_presentation)
            
            # Average total score
            mentor_total = mentor_eval.total_score if mentor_eval else 0
            coordinator_total = coordinator_eval.total_score if coordinator_eval else 0
            avg_total_score = (mentor_total + coordinator_total) / 2 if (mentor_eval and coordinator_eval) else (mentor_total or coordinator_total)
            
            # Separate mentor and coordinator comments
            mentor_comments = mentor_eval.comments if mentor_eval and mentor_eval.comments else "None"
            coordinator_comments = coordinator_eval.comments if coordinator_eval and coordinator_eval.comments else "None"
            
            submission_evaluations[submission.submission_id] = {
                'quality': avg_quality,
                'methodology': avg_methodology,
                'presentation': avg_presentation,
                'total_score': avg_total_score,
                'submission': submission,
                'document_url': submission.document.url,
                'mentor_comments': mentor_comments,
                'coordinator_comments': coordinator_comments,
            }

    context = {
        'student': student,
        'team': team,
        'submissions': submissions,
        'announcements': announcements,
        'evaluations': evaluations,
        'unread_messages': unread_messages,
        'submission_evaluations': submission_evaluations,
    }
    return render(request, 'student_dashboard.html', context)

def submit_research(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.student = student
            submission.team = student.team
            submission.save()
            messages.success(request, 'Submission successful!')
            return redirect('GradifyPortal:student_dashboard', student_id=student_id)
    else:
        form = SubmissionForm()
    return render(request, 'submit_research.html', {'form': form, 'student': student})

def student_chat(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    mentor = student.team.mentor
    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            ChatMessage.objects.create(
                sender_student=student,
                recipient_mentor=mentor,
                message=form.cleaned_data['message']
            )
            return redirect('GradifyPortal:student_chat', student_id=student_id)
    else:
        form = ChatMessageForm()
    messages = ChatMessage.objects.filter(sender_student=student, recipient_mentor=mentor) | \
               ChatMessage.objects.filter(sender_mentor=mentor, recipient_student=student)
    messages.update(is_read=True)
    return render(request, 'student_chat.html', {'student': student, 'form': form, 'messages': messages.order_by('timestamp')})

# Mentor Views
def mentor_dashboard(request, mentor_id):
    mentor = get_object_or_404(Mentor, mentor_id=mentor_id)
    teams = Team.objects.filter(mentor=mentor)
    pending_submissions = Submission.objects.filter(team__in=teams, status__in=['pending', 'under_review'])
    approved_submissions = Submission.objects.filter(team__in=teams, status='mentor_approved')
    evaluations = Evaluation.objects.filter(submission__team__in=teams)
    unread_messages = ChatMessage.objects.filter(recipient_mentor=mentor, is_read=False).count()
    context = {
        'mentor': mentor,
        'pending_submissions': pending_submissions,
        'approved_submissions': approved_submissions,
        'evaluations': evaluations,
        'unread_messages': unread_messages,
    }
    return render(request, 'mentor_dashboard.html', context)

def review_submission(request, mentor_id, submission_id):
    mentor = get_object_or_404(Mentor, mentor_id=mentor_id)
    submission = get_object_or_404(Submission, submission_id=submission_id)
    if submission.status not in ['pending', 'under_review']:
        messages.error(request, 'This submission cannot be reviewed.')
        return redirect('GradifyPortal:mentor_dashboard', mentor_id=mentor_id)
    if request.method == 'POST':
        form = ReviewForm(request.POST, instance=submission)
        if form.is_valid():
            submission.status = form.cleaned_data['status']
            submission.mentor_feedback = form.cleaned_data['mentor_feedback']
            if submission.status == 'mentor_approved':
                signature_text = f"{submission.document_hash}-{mentor.name}-{timezone.now().isoformat()}"
                submission.mentor_signature = hashlib.sha256(signature_text.encode()).hexdigest()
            else:
                submission.mentor_signature = None
            submission.save()
            action = "approved" if submission.status == 'mentor_approved' else "rejected"
            messages.success(request, f'Submission {action}!')
            return redirect('GradifyPortal:mentor_dashboard', mentor_id=mentor_id)
    else:
        form = ReviewForm(instance=submission)
    return render(request, 'review_submission.html', {'mentor': mentor, 'submission': submission, 'form': form})

def evaluate_submission(request, mentor_id, submission_id):
    mentor = get_object_or_404(Mentor, mentor_id=mentor_id)
    submission = get_object_or_404(Submission, submission_id=submission_id)
    if submission.status != 'mentor_approved':
        messages.error(request, 'Only approved submissions can be evaluated.')
        return redirect('GradifyPortal:mentor_dashboard', mentor_id=mentor_id)
    evaluation = Evaluation.objects.filter(submission=submission).first()
    if request.method == 'POST':
        form = EvaluationForm(request.POST, instance=evaluation)
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.evaluated_by_mentor = mentor  # Use evaluated_by_mentor
            evaluation.evaluated_by_coordinator = None  # Clear coordinator if set
            evaluation.submission = submission
            evaluation.save()
            messages.success(request, 'Evaluation submitted!')
            return redirect('GradifyPortal:mentor_dashboard', mentor_id=mentor_id)
    else:
        form = EvaluationForm(instance=evaluation) if evaluation else EvaluationForm()
    return render(request, 'evaluate_submission.html', {'mentor': mentor, 'submission': submission, 'form': form})

def mentor_chat(request, mentor_id):
    mentor = get_object_or_404(Mentor, mentor_id=mentor_id)
    students = Student.objects.filter(team__mentor=mentor)
    student_id = request.GET.get('student')
    student = get_object_or_404(Student, student_id=student_id) if student_id else students.first()
    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            ChatMessage.objects.create(
                sender_mentor=mentor,
                recipient_student=student,
                message=form.cleaned_data['message']
            )
            return redirect('GradifyPortal:mentor_chat', mentor_id=mentor_id)
    else:
        form = ChatMessageForm()
    messages = ChatMessage.objects.filter(sender_mentor=mentor, recipient_student=student) | \
               ChatMessage.objects.filter(sender_student=student, recipient_mentor=mentor)
    messages.update(is_read=True)
    return render(request, 'mentor_chat.html', {'mentor': mentor, 'students': students, 'student': student, 'form': form, 'messages': messages.order_by('timestamp')})

def create_announcement(request, mentor_id):
    mentor = get_object_or_404(Mentor, mentor_id=mentor_id)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = mentor.name  # Track who created it
            announcement.save()
            messages.success(request, 'Announcement posted!')
            return redirect('GradifyPortal:mentor_dashboard', mentor_id=mentor_id)
    else:
        form = AnnouncementForm()
    return render(request, 'create_announcement.html', {'mentor': mentor, 'form': form})

# Coordinator Views
def coordinator_dashboard(request, coordinator_id):
    coordinator = get_object_or_404(Coordinator, coordinator_id=coordinator_id)
    teams = Team.objects.filter(mentor__coordinator=coordinator)
    pending_approvals = Submission.objects.filter(team__in=teams, status='mentor_approved')
    # Show coordinator_approved submissions not yet evaluated by this coordinator
    submissions_to_evaluate = Submission.objects.filter(
        team__in=teams, 
        status='coordinator_approved'
    ).exclude(
        evaluation__evaluated_by_coordinator=coordinator
    )
    completed_evaluations = Evaluation.objects.filter(
        submission__team__in=teams, 
        evaluated_by_coordinator=coordinator
    )
    context = {
        'coordinator': coordinator,
        'pending_approvals': pending_approvals,
        'submissions_to_evaluate': submissions_to_evaluate,
        'completed_evaluations': completed_evaluations,
    }
    return render(request, 'coordinator_dashboard.html', context)

def coordinator_announcement(request, coordinator_id):
    coordinator = get_object_or_404(Coordinator, coordinator_id=coordinator_id)
    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.created_by = coordinator.name  # Track who created it
            announcement.save()
            messages.success(request, 'Announcement posted!')
            return redirect('GradifyPortal:coordinator_dashboard', coordinator_id=coordinator_id)
    else:
        form = AnnouncementForm()
    return render(request, 'coordinator_announcement.html', {'coordinator': coordinator, 'form': form})

def coordinator_approve_submission(request, coordinator_id, submission_id):
    coordinator = get_object_or_404(Coordinator, coordinator_id=coordinator_id)
    submission = get_object_or_404(Submission, submission_id=submission_id)
    if submission.status not in ['mentor_approved']:
        messages.error(request, 'This submission cannot be approved yet.')
        return redirect('GradifyPortal:coordinator_dashboard', coordinator_id=coordinator_id)
    if request.method == 'POST':
        form = ApprovalForm(request.POST, instance=submission)
        if form.is_valid():
            submission.status = form.cleaned_data['status']
            submission.coordinator_feedback = form.cleaned_data['coordinator_feedback']
            if submission.status == 'coordinator_approved':
                signature_text = f"{submission.document_hash}-{coordinator.name}-{timezone.now().isoformat()}"
                submission.coordinator_signature = hashlib.sha256(signature_text.encode()).hexdigest()
            else:
                submission.coordinator_signature = None
            submission.save()
            action = "approved" if submission.status == 'coordinator_approved' else "rejected"
            messages.success(request, f'Submission {action}!')
            return redirect('GradifyPortal:coordinator_dashboard', coordinator_id=coordinator_id)
    else:
        form = ApprovalForm(instance=submission)
    return render(request, 'coordinator_approve_submission.html', {
        'coordinator': coordinator,
        'submission': submission,
        'form': form,
    })

def coordinator_evaluate_submission(request, coordinator_id, submission_id):
    coordinator = get_object_or_404(Coordinator, coordinator_id=coordinator_id)
    submission = get_object_or_404(Submission, submission_id=submission_id)
    
    # Check for existing coordinator evaluation
    existing_eval = Evaluation.objects.filter(
        submission=submission, 
        evaluated_by_coordinator=coordinator
    ).first()
    
    # Ensure submission is coordinator_approved
    if submission.status != 'coordinator_approved':
        messages.error(request, "This submission is not yet approved for evaluation.")
        return redirect('GradifyPortal:coordinator_dashboard', coordinator_id=coordinator_id)
    
    if request.method == "POST":
        if existing_eval:
            # Update existing evaluation
            form = EvaluationForm(request.POST, instance=existing_eval)
        else:
            # Create new evaluation
            form = EvaluationForm(request.POST)
        
        if form.is_valid():
            evaluation = form.save(commit=False)
            evaluation.submission = submission
            evaluation.evaluated_by_coordinator = coordinator
            evaluation.evaluated_by_mentor = None  # Coordinator evaluation only
            evaluation.save()
            messages.success(request, "Evaluation submitted successfully.")
            return redirect('GradifyPortal:coordinator_dashboard', coordinator_id=coordinator_id)
    else:
        form = EvaluationForm(instance=existing_eval) if existing_eval else EvaluationForm()

    request.session['user_id'] = coordinator_id
    request.session['user_type'] = 'coordinator'

    return render(request, 'evaluate_submission.html', {
        'submission': submission,
        'form': form,
    })

def list_submissions(request):
    submissions_dir = os.path.join(settings.MEDIA_ROOT, 'submissions')
    files = []
    if os.path.exists(submissions_dir):
        files = [f for f in os.listdir(submissions_dir) if f.endswith('.pdf')]
    file_urls = [
        {'name': f, 'url': f"{settings.MEDIA_URL}submissions/{f}"}
        for f in files
    ]
    context = {
        'files': file_urls,
        'directory': 'Submissions',
    }
    return render(request, 'list_submissions.html', context)

# Include link_all_users and my_team variations
def link_all_users():
    # Students
    print("Linking students...")
    for student in Student.objects.all():
        try:
            if not hasattr(student, 'user') or student.user is None:
                user, created = User.objects.get_or_create(username=student.student_id)
                if created:
                    user.set_password('Gradify2025')
                    user.save()
                student.user = user
                student.save()
                print(f"Linked student {student.student_id} to User {user.username}")
            else:
                print(f"Student {student.student_id} already linked to {student.user}")
        except Exception as e:
            print(f"Error linking student {student.student_id}: {e}")

    # Mentors
    print("Linking mentors...")
    for mentor in Mentor.objects.all():
        try:
            if not hasattr(mentor, 'user') or mentor.user is None:
                user, created = User.objects.get_or_create(username=str(mentor.mentor_id))
                if created:
                    user.set_password('Gradify2025')
                    user.save()
                mentor.user = user
                mentor.save()
                print(f"Linked mentor {mentor.mentor_id} to User {user.username}")
            else:
                print(f"Mentor {mentor.mentor_id} already linked to {mentor.user}")
        except Exception as e:
            print(f"Error linking mentor {mentor.mentor_id}: {e}")

    # Coordinators
    print("Linking coordinators...")
    for coordinator in Coordinator.objects.all():
        try:
            if not hasattr(coordinator, 'user') or coordinator.user is None:
                user, created = User.objects.get_or_create(username=str(coordinator.coordinator_id))
                if created:
                    user.set_password('Gradify2025')
                    user.save()
                coordinator.user = user
                coordinator.save()
                print(f"Linked coordinator {coordinator.coordinator_id} to User {user.username}")
            else:
                print(f"Coordinator {coordinator.coordinator_id} already linked to {coordinator.user}")
        except Exception as e:
            print(f"Error linking coordinator {coordinator.coordinator_id}: {e}")

def is_student(user):
    return hasattr(user, 'student')

def is_mentor(user):
    return hasattr(user, 'mentor')

def is_coordinator(user):
    return hasattr(user, 'coordinator')

@login_required
def my_team(request):
    user = request.user
    context = {}

    if is_student(user):
        student = user.student
        if student.team:
            context['role'] = 'student'
            context['team'] = student.team
            context['current_student'] = student  # Add your own info
            context['teammates'] = Student.objects.filter(team=student.team).exclude(student_id=student.student_id)
            context['mentor'] = student.team.mentor
            context['coordinator'] = student.team.mentor.coordinator
        else:
            context['error'] = "You are not assigned to a team yet."

    elif is_mentor(user):
        mentor = user.mentor
        context['role'] = 'mentor'
        context['teams'] = Team.objects.filter(mentor=mentor)
        context['coordinator'] = mentor.coordinator
        if not context['teams']:
            context['error'] = "You have no teams assigned."

    elif is_coordinator(user):
        coordinator = user.coordinator
        context['role'] = 'coordinator'
        context['mentors'] = Mentor.objects.filter(coordinator=coordinator)
        context['teams'] = Team.objects.filter(mentor__coordinator=coordinator)
        if not context['mentors']:
            context['error'] = "You have no mentors or teams assigned."

    else:
        return HttpResponseForbidden("Access denied.")

    return render(request, 'my_team.html', context)


# Note: The two my_team functions are included as requested, though having two identical functions with the same name will cause a NameError. 
# You might want to rename one (e.g., my_team_alt) or remove one based on your needs.

# @login_required
# def my_team(request):
#     user = request.user
#     context = {}

#     if is_student(user):
#         student = user.student
#         if student.team:
#             context['role'] = 'student'
#             context['team'] = student.team
#             context['teammates'] = Student.objects.filter(team=student.team).exclude(student_id=student.student_id)
#             context['mentor'] = student.team.mentor
#             context['coordinator'] = student.team.mentor.coordinator
#         else:
#             context['error'] = "You are not assigned to a team yet."

#     elif is_mentor(user):
#         mentor = user.mentor
#         context['role'] = 'mentor'
#         context['teams'] = Team.objects.filter(mentor=mentor)
#         context['coordinator'] = mentor.coordinator
#         if not context['teams']:
#             context['error'] = "You have no teams assigned."

#     elif is_coordinator(user):
#         coordinator = user.coordinator
#         context['role'] = 'coordinator'
#         context['mentors'] = Mentor.objects.filter(coordinator=coordinator)
#         context['teams'] = Team.objects.filter(mentor__coordinator=coordinator)
#         if not context['mentors']:
#             context['error'] = "You have no mentors or teams assigned."

#     else:
#         return HttpResponseForbidden("Access denied.")

#     return render(request, 'my_team.html', context)



# Note: The two my_team functions are included as requested, though having two identical functions with the same name will cause a NameError. 
# You might want to rename one (e.g., my_team_alt) or remove one based on your needs.




# @login_required
# def my_team(request):
#     user = request.user
#     context = {}

#     if is_student(user):
#         student = user.student
#         if student.team:
#             context['role'] = 'student'
#             context['team'] = student.team
#             context['teammates'] = Student.objects.filter(team=student.team).exclude(student_id=student.student_id)
#             context['mentor'] = student.team.mentor
#             context['coordinator'] = student.team.mentor.coordinator
#         else:
#             context['error'] = "You are not assigned to a team yet."

#     elif is_mentor(user):
#         mentor = user.mentor
#         context['role'] = 'mentor'
#         context['teams'] = Team.objects.filter(mentor=mentor)
#         context['coordinator'] = mentor.coordinator
#         if not context['teams']:
#             context['error'] = "You have no teams assigned."

#     elif is_coordinator(user):
#         coordinator = user.coordinator
#         context['role'] = 'coordinator'
#         context['mentors'] = Mentor.objects.filter(coordinator=coordinator)
#         context['teams'] = Team.objects.filter(mentor__coordinator=coordinator)
#         if not context['mentors']:
#             context['error'] = "You have no mentors or teams assigned."

#     else:
#         return HttpResponseForbidden("Access denied.")

#     return render(request, 'my_team.html', context)

#<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<LINKS ALL THE USERS TO THEIR ROLES>>>>>>>>>>>>>>>>>>>>>>>>>>>
# def link_all_users():
#     # Students
#     print("Linking students...")
#     for student in Student.objects.all():
#         try:
#             if not hasattr(student, 'user') or student.user is None:
#                 user, created = User.objects.get_or_create(username=student.student_id)
#                 if created:
#                     user.set_password('Gradify2025')
#                     user.save()
#                 student.user = user
#                 student.save()
#                 print(f"Linked student {student.student_id} to User {user.username}")
#             else:
#                 print(f"Student {student.student_id} already linked to {student.user}")
#         except Exception as e:
#             print(f"Error linking student {student.student_id}: {e}")

#     # Mentors
#     print("Linking mentors...")
#     for mentor in Mentor.objects.all():
#         try:
#             if not hasattr(mentor, 'user') or mentor.user is None:
#                 user, created = User.objects.get_or_create(username=str(mentor.mentor_id))
#                 if created:
#                     user.set_password('Gradify2025')
#                     user.save()
#                 mentor.user = user
#                 mentor.save()
#                 print(f"Linked mentor {mentor.mentor_id} to User {user.username}")
#             else:
#                 print(f"Mentor {mentor.mentor_id} already linked to {mentor.user}")
#         except Exception as e:
#             print(f"Error linking mentor {mentor.mentor_id}: {e}")

#     # Coordinators
#     print("Linking coordinators...")
#     for coordinator in Coordinator.objects.all():
#         try:
#             if not hasattr(coordinator, 'user') or coordinator.user is None:
#                 user, created = User.objects.get_or_create(username=str(coordinator.coordinator_id))
#                 if created:
#                     user.set_password('Gradify2025')
#                     user.save()
#                 coordinator.user = user
#                 coordinator.save()
#                 print(f"Linked coordinator {coordinator.coordinator_id} to User {user.username}")
#             else:
#                 print(f"Coordinator {coordinator.coordinator_id} already linked to {coordinator.user}")
#         except Exception as e:
#             print(f"Error linking coordinator {coordinator.coordinator_id}: {e}")

# #<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>

# @login_required
# def create_task(request, id):
#     user = request.user
#     if hasattr(user, 'mentor'):
#         mentor = get_object_or_404(Mentor, mentor_id=id, user=user)
#         teams = Team.objects.filter(mentor=mentor)
#     elif hasattr(user, 'coordinator'):
#         coordinator = get_object_or_404(Coordinator, coordinator_id=id, user=user)
#         teams = Team.objects.filter(mentor__coordinator=coordinator)
#     else:
#         return HttpResponseForbidden("Access denied.")

#     if request.method == 'POST':
#         form = TaskForm(request.POST)
#         if form.is_valid():
#             task = form.save(commit=False)
#             task.created_by = user
#             task.save()
#             messages.success(request, "Task created successfully.")
#             if hasattr(user, 'mentor'):
#                 return redirect('GradifyPortal:mentor_dashboard', mentor_id=id)
#             return redirect('GradifyPortal:coordinator_dashboard', coordinator_id=id)
#     else:
#         form = TaskForm()
#         form.fields['team'].queryset = teams

#     return render(request, 'create_task.html', {'form': form})