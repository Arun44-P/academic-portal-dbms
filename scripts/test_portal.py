import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model

User = get_user_model()
client = Client()

print("=" * 65)
print("TESTING ACADEMIC MANAGEMENT PORTAL (RESEARCH REMOVAL VERIFICATION)")
print("=" * 65)

# 1. Test root & login
res = client.get('/')
print(f"GET / -> Status {res.status_code} (Redirects to: {res.url})")
assert res.status_code == 302

res = client.get('/accounts/login/')
print(f"GET /accounts/login/ -> Status {res.status_code}")
assert res.status_code == 200
login_html = res.content.decode('utf-8')
assert "Academic Management Portal" in login_html
assert "Research Fellowship Grants" not in login_html
print("Login branding verified: 'Academic Management Portal' (Research references removed)")

# 2. Test Student Role (atharv_pathak)
print("\n--- Testing Student Role (atharv_pathak) ---")
logged_in = client.login(username='atharv_pathak', password='pass123')
print(f"Login atharv_pathak: {logged_in}")
assert logged_in

student_routes = [
    '/student-portal/dashboard/',
    '/student-portal/courses/',
    '/student-portal/catalog/',
    '/student-portal/attendance-grades/',
    '/student-portal/fee-status/',
]
for route in student_routes:
    res = client.get(route)
    print(f"GET {route} -> Status {res.status_code}")
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert "Research Assistantship" not in html
    assert "Research Junior Status" not in html
    assert "Research Fellow Attached" not in html

# Verify old research route redirects to student dashboard
res = client.get('/student-portal/research-role/')
print(f"GET /student-portal/research-role/ -> Status {res.status_code} (Redirects to: {res.url})")
assert res.status_code == 302
assert '/student-portal/dashboard/' in res.url

client.logout()

# 3. Test Faculty Role (dr_sahu)
print("\n--- Testing Faculty Role (dr_sahu) ---")
logged_in = client.login(username='dr_sahu', password='pass123')
print(f"Login dr_sahu: {logged_in}")
assert logged_in

faculty_routes = [
    '/faculty-portal/dashboard/',
    '/faculty-portal/sections/',
    '/faculty-portal/attendance/',
    '/faculty-portal/marks/',
]
for route in faculty_routes:
    res = client.get(route)
    print(f"GET {route} -> Status {res.status_code}")
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert "Research Wing" not in html
    assert "Grants &amp; Projects" not in html
    assert "Junior Fellows &amp; Stipends" not in html
    assert "Research Publications" not in html
    assert "Active Research Grants" not in html
    assert "Attached Research Fellows" not in html

# Verify old faculty research routes redirect to faculty dashboard
disabled_faculty_routes = [
    '/faculty-portal/research-projects/',
    '/faculty-portal/research-juniors/',
    '/faculty-portal/publications/',
    '/faculty-portal/stipend/approve/1/',
]
for route in disabled_faculty_routes:
    res = client.get(route)
    print(f"GET {route} -> Status {res.status_code} (Redirects to: {res.url})")
    assert res.status_code == 302
    assert '/faculty-portal/dashboard/' in res.url

client.logout()

# 4. Test Office Staff Role (staff_sunita)
print("\n--- Testing Office Staff Role (staff_sunita) ---")
logged_in = client.login(username='staff_sunita', password='pass123')
print(f"Login staff_sunita: {logged_in}")
assert logged_in

office_routes = [
    '/office-portal/dashboard/',
    '/office-portal/schedule/',
]
for route in office_routes:
    res = client.get(route)
    print(f"GET {route} -> Status {res.status_code}")
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert "Stipend Disbursement" not in html
    assert "Stipends in Accounts Queue" not in html
    assert "Stipends Awaiting Bank Transfer" not in html

# Verify old office stipend queue route redirects to office dashboard
res = client.get('/office-portal/stipend-queue/')
print(f"GET /office-portal/stipend-queue/ -> Status {res.status_code} (Redirects to: {res.url})")
assert res.status_code == 302
assert '/office-portal/dashboard/' in res.url

client.logout()

# 5. Test Admin Role (admin)
print("\n--- Testing Admin Role (admin) ---")
logged_in = client.login(username='admin', password='pass123')
print(f"Login admin: {logged_in}")
assert logged_in

admin_routes = [
    '/admin-portal/dashboard/',
    '/admin-portal/console/',
    '/admin-portal/users/',
    '/admin-portal/audit-logs/',
]
for route in admin_routes:
    res = client.get(route)
    print(f"GET {route} -> Status {res.status_code}")
    assert res.status_code == 200
    html = res.content.decode('utf-8')
    assert "Active Research Funding" not in html
    assert "research grant pools" not in html

client.logout()

print("\n" + "=" * 65)
print("ALL VERIFICATION CHECKS PASSED: RESEARCH MODULE FULLY REMOVED!")
print("=" * 65)
