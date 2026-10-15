from django.urls import path
from apps.academics import views

app_name = 'office'

urlpatterns = [
    path('dashboard/', views.office_dashboard, name='dashboard'),
    path('stipend/disburse/<int:disbursement_id>/', views.disburse_stipend, name='disburse_stipend'),
]
