from django.urls import path
from apps.core_admin import views

app_name = 'core_admin'

urlpatterns = [
    path('dashboard/', views.admin_dashboard, name='dashboard'),
    path('console/', views.database_console, name='database_console'),
    path('execute-radical-action/', views.execute_radical_action, name='execute_radical_action'),
    path('users/', views.user_directory, name='users'),
    path('user-directory/', views.user_directory, name='user_directory'),
    path('users/<int:user_id>/toggle/', views.toggle_user_status, name='toggle_user_status'),
    path('audit-logs/', views.audit_logs, name='audit_logs'),
]
