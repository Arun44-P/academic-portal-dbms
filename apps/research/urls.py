from django.urls import path
from apps.research import views

app_name = 'faculty'

urlpatterns = [
    path('dashboard/', views.faculty_dashboard, name='dashboard'),
    path('section/<int:offering_id>/roster/', views.section_roster, name='section_roster'),
    path('stipend/approve/<int:disbursement_id>/', views.approve_stipend, name='approve_stipend'),
]
