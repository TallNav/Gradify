# GradifyPortal/admin.py
import csv
from django.contrib import admin
from django.shortcuts import render, redirect
from django.urls import path
from .models import Student, Team, Mentor, Coordinator, Section, Submission, Announcement, Evaluation
from .forms import StudentUploadForm, MentorUploadForm, CoordinatorUploadForm
from django.contrib.auth.hashers import make_password

# Custom Student Admin
class StudentAdmin(admin.ModelAdmin):
    list_display = ('student_id', 'name', 'team', 'section', 'email')
    search_fields = ('student_id', 'name', 'email')
    search_help_text = "Search by student ID, name, or email (e.g., 'Naruto', 'NAR-A-001')."

# Custom Team Admin with Student CSV Upload
class TeamAdmin(admin.ModelAdmin):
    list_display = ('team_id', 'mentor', 'section')
    search_fields = ('team_id', 'mentor__name', 'section__section_id')
    search_help_text = "Search by team ID, mentor name, or section (e.g., 'CSE-C23', 'Kakashi')."
    actions = ['upload_students_teams']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-students-teams/', self.admin_site.admin_view(self.upload_students_teams_view), name='upload_students_teams'),
        ]
        return custom_urls + urls

    def upload_students_teams(self, request, queryset):
        """Action to trigger the student upload form"""
        return redirect('admin:upload_students_teams')

    upload_students_teams.short_description = "Upload Students and Teams via CSV"

    def upload_students_teams_view(self, request):
        if request.method == 'POST':
            form = StudentUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)

                # Debug: Print CSV headers
                print("CSV headers:", reader.fieldnames)

                # Validate CSV headers
                required_fields = {'section', 'batch id', 'name', 'roll no', 'mentor allotted', 'coordinator allotted', 'gmailid'}
                if not required_fields.issubset(reader.fieldnames):
                    error_msg = f"CSV must include {required_fields} columns. Got: {reader.fieldnames}"
                    print(error_msg)
                    return render(request, 'team_upload.html', {
                        'form': form,
                        'error': error_msg
                    })

                # Process each row
                for row in reader:
                    print("Processing row:", row)
                    section_id = row['section']
                    batch_id = row['batch id']
                    student_id = row['roll no']
                    name = row['name']
                    mentor_id = row['mentor allotted']
                    coordinator_id = row['coordinator allotted']
                    email = row['gmailid']

                    # Validate/Create Section
                    if section_id not in ['A', 'B', 'C', 'D', 'E']:
                        section_id = 'A'
                    section, _ = Section.objects.get_or_create(section_id=section_id)

                    # Get Mentor and Coordinator
                    try:
                        mentor = Mentor.objects.get(mentor_id=mentor_id)
                        print(f"Found mentor: {mentor_id} - {mentor.name}")
                    except Mentor.DoesNotExist:
                        error_msg = f"Invalid Mentor ID: {mentor_id}. Ensure mentors are uploaded first."
                        print(error_msg)
                        return render(request, 'team_upload.html', {
                            'form': form,
                            'error': error_msg
                        })
                    try:
                        coordinator = Coordinator.objects.get(coordinator_id=coordinator_id)
                        print(f"Found coordinator: {coordinator_id} - {coordinator.name}")
                    except Coordinator.DoesNotExist:
                        error_msg = f"Invalid Coordinator ID: {coordinator_id}. Ensure coordinators are uploaded first."
                        print(error_msg)
                        return render(request, 'team_upload.html', {
                            'form': form,
                            'error': error_msg
                        })

                    # Create/Get Team
                    team_id = f"CSE-{batch_id.upper()}"  # e.g., CSE-C23
                    team, _ = Team.objects.get_or_create(
                        team_id=team_id,
                        defaults={'mentor': mentor, 'section': section}
                    )

                    # Create/Update Student
                    try:
                        Student.objects.update_or_create(
                            student_id=student_id,
                            defaults={
                                'name': name,
                                'email': email,
                                'team': team,
                                'section': section,
                                'password': make_password("Gradify2025")
                            }
                        )
                        print(f"Successfully processed student: {student_id}")
                    except Exception as e:
                        print(f"Error saving student {student_id}: {str(e)}")
                        return render(request, 'team_upload.html', {
                            'form': form,
                            'error': f"Error saving student {student_id}: {str(e)}"
                        })

                return redirect('admin:GradifyPortal_team_changelist')
            else:
                error_message = f"Form errors: {form.errors.as_text()}"
                print(error_message)
                return render(request, 'team_upload.html', {
                    'form': form,
                    'error': error_message
                })
        else:
            form = StudentUploadForm()
        return render(request, 'team_upload.html', {'form': form})

# Custom Mentor Admin with CSV Upload
class MentorAdmin(admin.ModelAdmin):
    list_display = ('mentor_id', 'name', 'email', 'coordinator')
    search_fields = ('mentor_id', 'name', 'email', 'coordinator__name')
    search_help_text = "Search by mentor ID, name, email, or coordinator name (e.g., 'Kakashi', '1001', 'Hiruzen')."
    actions = ['upload_mentors']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-mentors/', self.admin_site.admin_view(self.upload_mentors_view), name='upload_mentors'),
        ]
        return custom_urls + urls

    def upload_mentors(self, request, queryset):
        """Action to trigger the mentor upload form"""
        return redirect('admin:upload_mentors')

    upload_mentors.short_description = "Upload Mentors via CSV"

    def upload_mentors_view(self, request):
        if request.method == 'POST':
            form = MentorUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)

                # Debug: Print CSV headers
                print("CSV headers:", reader.fieldnames)

                # Validate CSV headers
                required_fields = {'mentor id', 'name', 'gmailid', 'coordinator id'}
                if not required_fields.issubset(reader.fieldnames):
                    error_msg = f"CSV must include {required_fields} columns. Got: {reader.fieldnames}"
                    print(error_msg)
                    return render(request, 'mentor_upload.html', {
                        'form': form,
                        'error': error_msg
                    })

                # Process each row
                for row in reader:
                    print("Processing row:", row)  # Debug: Print row data
                    mentor_id = row['mentor id']
                    name = row['name']
                    email = row['gmailid']
                    coordinator_id = row['coordinator id']

                    # Validate Coordinator
                    try:
                        coordinator = Coordinator.objects.get(coordinator_id=coordinator_id)
                        print(f"Found coordinator: {coordinator_id} - {coordinator.name}")
                    except Coordinator.DoesNotExist:
                        error_msg = f"Invalid Coordinator ID: {coordinator_id}. Ensure coordinators are uploaded first."
                        print(error_msg)
                        return render(request, 'mentor_upload.html', {
                            'form': form,
                            'error': error_msg
                        })

                    # Create/Update Mentor
                    try:
                        Mentor.objects.update_or_create(
                            mentor_id=mentor_id,
                            defaults={
                                'name': name,
                                'email': email,
                                'coordinator': coordinator,
                                'password': make_password("Gradify2025")
                            }
                        )
                        print(f"Successfully processed mentor: {mentor_id}")
                    except Exception as e:
                        print(f"Error saving mentor {mentor_id}: {str(e)}")
                        return render(request, 'mentor_upload.html', {
                            'form': form,
                            'error': f"Error saving mentor {mentor_id}: {str(e)}"
                        })

                return redirect('admin:GradifyPortal_mentor_changelist')
            else:
                error_message = f"Form errors: {form.errors.as_text()}"
                print(error_message)
                return render(request, 'mentor_upload.html', {
                    'form': form,
                    'error': error_message
                })
        else:
            form = MentorUploadForm()
        return render(request, 'mentor_upload.html', {'form': form})

# Custom Coordinator Admin with CSV Upload
class CoordinatorAdmin(admin.ModelAdmin):
    list_display = ('coordinator_id', 'name', 'email')
    search_fields = ('coordinator_id', 'name', 'email')
    search_help_text = "Search by coordinator ID, name, or email (e.g., 'Hiruzen', '501')."
    actions = ['upload_coordinators']

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-coordinators/', self.admin_site.admin_view(self.upload_coordinators_view), name='upload_coordinators'),
        ]
        return custom_urls + urls

    def upload_coordinators(self, request, queryset):
        """Action to trigger the coordinator upload form"""
        return redirect('admin:upload_coordinators')

    upload_coordinators.short_description = "Upload Coordinators via CSV"

    def upload_coordinators_view(self, request):
        if request.method == 'POST':
            form = CoordinatorUploadForm(request.POST, request.FILES)
            if form.is_valid():
                csv_file = request.FILES['csv_file']
                decoded_file = csv_file.read().decode('utf-8').splitlines()
                reader = csv.DictReader(decoded_file)

                # Validate CSV headers
                required_fields = {'coordinator id', 'name', 'gmailid'}
                if not required_fields.issubset(reader.fieldnames):
                    return render(request, 'coordinator_upload.html', {
                        'form': form,
                        'error': 'CSV must include "coordinator id", "name", and "gmailid" columns.'
                    })

                # Process each row
                for row in reader:
                    coordinator_id = row['coordinator id']
                    name = row['name']
                    email = row['gmailid']

                    # Create/Update Coordinator
                    Coordinator.objects.update_or_create(
                        coordinator_id=coordinator_id,
                        defaults={
                            'name': name,
                            'email': email,
                            'password': make_password("Gradify2025")
                        }
                    )

                return redirect('admin:GradifyPortal_coordinator_changelist')
            else:
                return render(request, 'coordinator_upload.html', {'form': form, 'error': 'Please upload a valid CSV file.'})
        else:
            form = CoordinatorUploadForm()
        return render(request, 'coordinator_upload.html', {'form': form})

# Custom Admin for Other Models
class SectionAdmin(admin.ModelAdmin):
    list_display = ('section_id',)
    search_fields = ('section_id',)
    search_help_text = "Search by section ID (e.g., 'A', 'B')."

class SubmissionAdmin(admin.ModelAdmin):
    list_display = ('title', 'student', 'team', 'status', 'submitted_at')
    search_fields = ('title', 'student__name', 'team__team_id', 'status')
    search_help_text = "Search by submission title, student name, team ID, or status (e.g., 'Research', 'Naruto', 'mentor_approved')."

class AnnouncementAdmin(admin.ModelAdmin):
    list_display = ('title',)  # Minimal safe field
    search_fields = ('title',)  # Minimal safe field
    search_help_text = "Search by announcement title (e.g., 'Update')."

class EvaluationAdmin(admin.ModelAdmin):
    list_display = ('submission', 'total_score')
    search_fields = ('submission__title',)
    search_help_text = "Search by submission title (e.g., 'Research')."

# Register Models with Custom Admin Classes
admin.site.register(Student, StudentAdmin)
admin.site.register(Team, TeamAdmin)
admin.site.register(Mentor, MentorAdmin)
admin.site.register(Coordinator, CoordinatorAdmin)
admin.site.register(Section, SectionAdmin)
admin.site.register(Submission, SubmissionAdmin)
admin.site.register(Announcement, AnnouncementAdmin)
admin.site.register(Evaluation, EvaluationAdmin)