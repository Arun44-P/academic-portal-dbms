from django.urls import path
from apps.academics import views

app_name = 'office'

urlpatterns = [
    path('dashboard/', views.office_dashboard, name='dashboard'),
    path('stipend-queue/', views.stipend_queue_view, name='stipend_queue'),
    path('schedule/', views.schedule_view, name='schedule'),
    path('stipend/disburse/<int:disbursement_id>/', views.disburse_stipend, name='disburse_stipend'),
]
