import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
import django
django.setup()

from django.test import Client
from apps.accounts.models import UserAccount

def verify_student():
    client = Client()
    logged_in = client.login(username='atharv_pathak', password='pass123')
    assert logged_in, "Failed to login as atharv_pathak"
    print("[OK] Logged in as student atharv_pathak")

    # 1. Student Dashboard
    res_dash = client.get('/student-portal/dashboard/')
    assert res_dash.status_code == 200, f"Dashboard returned {res_dash.status_code}"
    print("[OK] Student Dashboard returned 200 OK")

    # 2. Attendance & Grades
    res_grades = client.get('/student-portal/attendance-grades/')
    assert res_grades.status_code == 200, f"Attendance & Grades returned {res_grades.status_code}"
    html = res_grades.content.decode()
    assert 'Mid-Term Exam' in html, "Published assessment 'Mid-Term Exam' not found in student view"
    assert 'Draft Quiz 1' not in html, "SECURITY LEAK: Unpublished 'Draft Quiz 1' leaked into student view"
    print("[OK] Published assessment displayed; Draft assessments strictly excluded!")

    # 3. Unauthorized access to admin portal views
    res_admin = client.get('/admin-portal/dashboard/')
    assert res_admin.status_code == 403, f"Admin dashboard returned {res_admin.status_code} instead of 403"
    print("[OK] Student blocked from Admin Dashboard with HTTP 403 Forbidden")

    print("\nALL PHASE 3 STUDENT PERMISSION VERIFICATIONS PASSED!")

if __name__ == '__main__':
    verify_student()

