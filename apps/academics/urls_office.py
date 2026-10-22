from django.urls import path
from apps.academics import views

app_name = 'office'

urlpatterns = [
    path('dashboard/', views.office_dashboard, name='dashboard'),
    path('fee-records/', views.office_dashboard, name='fee_records'),
    path('payments/', views.office_payment_history, name='payment_history'),
    path('fee-account/<int:account_id>/', views.student_fee_detail_view, name='fee_detail'),
    path('fee-account/<int:account_id>/record-payment/', views.record_fee_payment, name='record_payment'),
    path('schedule/', views.schedule_view, name='schedule'),
    # Legacy research endpoints redirected safely
    path('stipend-queue/', views.stipend_queue_view, name='stipend_queue'),
    path('stipend/disburse/<int:disbursement_id>/', views.disburse_stipend, name='disburse_stipend'),
]
