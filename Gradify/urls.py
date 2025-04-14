# Gradify/urls.py
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, re_path, include
from django.views.static import serve
from GradifyPortal import views
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('GradifyPortal.urls')),
    # Specific route for listing submissions
    path('media/submissions/', views.list_submissions, name='list_submissions'),
    # Generic media serving for individual files
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Optional: Keep static() for development fallback
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)