from django.urls import path
from apps.academics import views

app_name = 'student'

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='dashboard'),
    path('courses/', views.course_catalog, name='courses'),
    path('catalog/', views.course_catalog, name='catalog'),
    path('attendance-grades/', views.student_attendance_grades, name='attendance_grades'),
    path('fee-status/', views.student_fee_status, name='fee_status'),
    path('research-role/', views.student_research_role, name='research_role'),
    path('enroll/<int:offering_id>/', views.enroll_course, name='enroll_course'),
    path('drop/<int:enrollment_id>/', views.drop_course, name='drop_course'),
]
