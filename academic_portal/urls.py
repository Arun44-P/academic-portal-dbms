from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('accounts:login'), name='root'),
    path('django-admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('admin-portal/', include(('apps.core_admin.urls', 'core_admin'), namespace='core_admin')),
    path('faculty-portal/', include(('apps.research.urls', 'faculty'), namespace='faculty')),
    path('teacher-alias/', include(('apps.research.urls', 'teacher'), namespace='teacher')),
    path('office-portal/', include('apps.academics.urls_office')),
    path('student-portal/', include('apps.academics.urls_student')),
]
