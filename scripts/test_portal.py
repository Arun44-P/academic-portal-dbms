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

print("=" * 60)
print("TESTING PORTAL AUTHENTICATION & ALL ROLE ROUTES")
print("=" * 60)

# 1. Test root & login
res = client.get('/')
print(f"GET / -> Status {res.status_code} (Redirects to: {res.url})")
assert res.status_code == 302

res = client.get('/accounts/login/')
print(f"GET /accounts/login/ -> Status {res.status_code}")
assert res.status_code == 200

# 2. Test Student Arjun
print("\n--- Testing Student Role (student_arjun) ---")
logged_in = client.login(username='student_arjun', password='pass123')
print(f"Login student_arjun: {logged_in}")
assert logged_in

student_routes = [
    '/student-portal/dashboard/',
    '/student-portal/courses/',
    '/student-portal/catalog/',
    '/student-portal/attendance-grades/',
    '/student-portal/research-role/',
]
for route in student_routes:
    res = client.get(route)
    print(f"GET {route} -> Status {res.status_code}")
    assert res.status_code == 200

client.logout()

# 3. Test Faculty Dr. Sharma
print("\n--- Testing Faculty Role (dr_sharma) ---")
logged_in = client.login(username='dr_sharma', password='pass123')
print(f"Login dr_sharma: {logged_in}")
assert logged_in

faculty_routes = [
    '/faculty-portal/dashboard/',
    '/faculty-portal/sections/',
    '/faculty-portal/attendance/',
    '/faculty-portal/marks/',
    '/faculty-portal/research-projects/',
    '/faculty-portal/research-juniors/',
    '/faculty-portal/publications/',
]
for route in faculty_routes:
    res = client.get(route)
    print(f"GET {route} -> Status {res.status_code}")
    assert res.status_code == 200

client.logout()

# 4. Test Office Staff Sunita
print("\n--- Testing Office Staff Role (staff_sunita) ---")
logged_in = client.login(username='staff_sunita', password='pass123')
print(f"Login staff_sunita: {logged_in}")
assert logged_in

office_routes = [
    '/office-portal/dashboard/',
    '/office-portal/stipend-queue/',
    '/office-portal/schedule/',
]
for route in office_routes:
    res = client.get(route)
    print(f"GET {route} -> Status {res.status_code}")
    assert res.status_code == 200

client.logout()

# 5. Test Admin
print("\n--- Testing Admin Role (admin) ---")
logged_in = client.login(username='admin', password='admin123')
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

client.logout()

print("\n" + "=" * 60)
print("ALL 19 ROUTES PASSED WITH STATUS 200 OK!")
print("=" * 60)
