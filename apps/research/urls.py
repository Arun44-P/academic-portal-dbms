from django.urls import path
from apps.research import views

app_name = 'faculty'

urlpatterns = [
    path('dashboard/', views.faculty_dashboard, name='dashboard'),
    path('sections/', views.sections_view, name='sections'),
    path('attendance/', views.attendance_entry_view, name='attendance_entry'),
    path('marks/', views.marks_entry_view, name='marks_entry'),
    path('research-projects/', views.research_projects_view, name='research_projects'),
    path('research-juniors/', views.research_juniors_view, name='research_juniors'),
    path('publications/', views.publications_view, name='publications'),
    path('section/<int:offering_id>/roster/', views.section_roster, name='section_roster'),
    path('stipend/approve/<int:disbursement_id>/', views.approve_stipend, name='approve_stipend'),
]
