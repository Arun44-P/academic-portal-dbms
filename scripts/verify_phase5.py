import os, sys
from pathlib import Path
BASE_DIR = Path.cwd()
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
import django
django.setup()

from django.test import Client

client = Client()
# 1. Login as Office Staff
assert client.login(username='staff_sunita', password='pass123')
print('[OK] Logged in as staff_sunita (OFFICE_STAFF)')

# 2. Access Student Directory
res_students = client.get('/office-portal/students/')
assert res_students.status_code == 200, f'Expected 200, got {res_students.status_code}'
assert 'Institutional Student Directory' in res_students.content.decode()
assert 'Atharv Pathak' in res_students.content.decode()
print('[OK] Office Student Directory returned 200 OK with real student records')

# 3. Access Faculty Directory
res_faculty = client.get('/office-portal/faculty/')
assert res_faculty.status_code == 200, f'Expected 200, got {res_faculty.status_code}'
assert 'Institutional Faculty Directory' in res_faculty.content.decode()
assert 'Yatendra Sahu' in res_faculty.content.decode()
print('[OK] Office Faculty Directory returned 200 OK with real faculty records')

# 4. Search and Filter
res_search = client.get('/office-portal/students/?q=Atharv')
assert res_search.status_code == 200
assert 'Atharv Pathak' in res_search.content.decode()
print('[OK] Student Directory Search verified')

# 5. Security Boundary Verification: Office staff must NOT access Faculty Marks/Attendance or Admin
res_att = client.get('/faculty-portal/attendance/')
assert res_att.status_code == 403, f'Expected 403, got {res_att.status_code}'
print('[OK] Office staff blocked from Faculty Attendance entry with HTTP 403 Forbidden')

res_marks = client.get('/faculty-portal/marks/')
assert res_marks.status_code == 403, f'Expected 403, got {res_marks.status_code}'
print('[OK] Office staff blocked from Faculty Marks entry with HTTP 403 Forbidden')

print('\n=== ALL PHASE 5 OFFICE STAFF PERMISSION VERIFICATIONS PASSED 100%! ===')

