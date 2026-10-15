from django.urls import path
from apps.academics import views

app_name = 'student'

urlpatterns = [
    path('dashboard/', views.student_dashboard, name='dashboard'),
    path('catalog/', views.course_catalog, name='catalog'),
    path('enroll/<int:offering_id>/', views.enroll_course, name='enroll_course'),
    path('drop/<int:enrollment_id>/', views.drop_course, name='drop_course'),
]
