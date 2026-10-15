from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('', lambda request: redirect('accounts:login'), name='root'),
    path('django-admin/', admin.site.urls),
    path('accounts/', include('apps.accounts.urls')),
    path('admin-portal/', include('apps.core_admin.urls')),
    path('faculty-portal/', include('apps.research.urls')),
    path('office-portal/', include('apps.academics.urls_office')),
    path('student-portal/', include('apps.academics.urls_student')),
]
