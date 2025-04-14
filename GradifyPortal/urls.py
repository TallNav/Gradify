# GradifyPortal/urls.py
from django.urls import path,include
from . import views
from django.contrib import admin

app_name = 'GradifyPortal'

urlpatterns = [

    #Admin
    path('admin/', admin.site.urls),
    path('debug-auth/', views.debug_auth, name='debug_auth'),
    path('',views.login_view,name = 'home'),
    # Authentication
    path('login', views.login_view, name='login'),
   # path('accounts/', include('django.contrib.auth.urls')),  # For login/logout
    path('accounts/login/',views.login_view, name = 'accounts_login'),
    path('logout/', views.logout_view, name='logout'),
    
    #Common my-team
    path('my_team/', views.my_team, name='my_team'),
    
    #tasks
    #path('mentor/<int:mentor_id>/task/', views.create_task, name='create_task'),
    #path('coordinator/<int:coordinator_id>/task/', views.create_task, name='coordinator_create_task'),

    # Student URLs
    path('student/<str:student_id>/', views.student_dashboard, name='student_dashboard'),
    path('student/<str:student_id>/submit/', views.submit_research, name='submit_research'),
    path('student/<str:student_id>/chat/', views.student_chat, name='student_chat'),

    # Mentor URLs
    path('mentor/<int:mentor_id>/', views.mentor_dashboard, name='mentor_dashboard'),
    path('mentor/<int:mentor_id>/review/<int:submission_id>/', views.review_submission, name='review_submission'),
    path('mentor/<int:mentor_id>/evaluate/<int:submission_id>/', views.evaluate_submission, name='evaluate_submission'),
    path('mentor/<int:mentor_id>/chat/', views.mentor_chat, name='mentor_chat'),
    path('mentor/<int:mentor_id>/announcement/', views.create_announcement, name='create_announcement'),

    # Coordinator URLs
    path('coordinator/<int:coordinator_id>/', views.coordinator_dashboard, name='coordinator_dashboard'),
    path('coordinator/<int:coordinator_id>/approve/<int:submission_id>/', views.coordinator_approve_submission, name='coordinator_approve_submission'),
    path('coordinator/<int:coordinator_id>/evaluate/<int:submission_id>/', views.coordinator_evaluate_submission, name='coordinator_evaluate_submission'),
    path('coordinator/<int:coordinator_id>/announcement/', views.coordinator_announcement, name='coordinator_announcement'),
]