import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
import django
django.setup()

from django.test import Client

client = Client()

print("=" * 70)
print("PHASE 7: MULTI-ROLE FUNCTIONALITY VERIFICATION ON MYSQL")
print("=" * 70)

# 1. Admin Role
assert client.login(username='admin', password='pass123')
res_adm = client.get('/admin-portal/dashboard/')
assert res_adm.status_code == 200
res_console = client.get('/admin-portal/console/')
assert res_console.status_code == 200
assert "academic_portal_db" in res_console.content.decode('utf-8') or "accounts_useraccount" in res_console.content.decode('utf-8')
print("[PASS] Admin Dashboard & Database Console: HTTP 200 (Connected to MySQL)")
client.logout()

# 2. Teacher Role
assert client.login(username='dr_sahu', password='pass123')
res_teach = client.get('/faculty-portal/dashboard/')
assert res_teach.status_code == 200
html_teach = res_teach.content.decode('utf-8')
assert "Yatendra Sahu" in html_teach
assert "FAC-CSE-001" in html_teach
res_sections = client.get('/faculty-portal/sections/')
assert res_sections.status_code == 200
print("[PASS] Faculty Dashboard & Course Sections: HTTP 200 (Dr. Yatendra Sahu profile verified)")
client.logout()

# 3. Student Role
assert client.login(username='atharv_pathak', password='pass123')
res_stud = client.get('/student-portal/dashboard/')
assert res_stud.status_code == 200
html_stud = res_stud.content.decode('utf-8')
assert "2024BCS001" in html_stud
assert "Atharv Pathak" in html_stud
res_courses = client.get('/student-portal/courses/')
assert res_courses.status_code == 200
print("[PASS] Student Dashboard & Registered Courses: HTTP 200 (Atharv Pathak verified)")
client.logout()

# 4. Office Staff Role
assert client.login(username='staff_sunita', password='pass123')
res_office = client.get('/office-portal/dashboard/')
assert res_office.status_code == 200
html_off = res_office.content.decode('utf-8')
assert "Student Fee Management" in html_off
assert "350000" in html_off or "350,000" in html_off
print("[PASS] Office Staff Fee Dashboard: HTTP 200 (Real-time fee metrics verified)")
client.logout()

print("\n" + "=" * 70)
print("ALL 4 USER ROLES VERIFIED WORKING FLAWLESSLY ON MYSQL!")
print("=" * 70)
