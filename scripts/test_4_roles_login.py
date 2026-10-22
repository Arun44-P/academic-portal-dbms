"""
Verify 4-Role Authentication, Dispatch, and Group Membership
"""
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
from apps.accounts.permissions import user_has_role

roles_to_test = [
    ('admin', 'ADMIN', '/admin-portal/dashboard/'),
    ('dr_sahu', 'FACULTY', '/faculty-portal/dashboard/'),
    ('staff_sunita', 'OFFICE_STAFF', '/office-portal/dashboard/'),
    ('atharv_pathak', 'STUDENT', '/student-portal/dashboard/'),
]

print("=== Testing 4 Primary Roles: Auth, Dispatch & Group RBAC ===")

for username, expected_role, expected_dashboard in roles_to_test:
    client = Client()
    user = UserAccount.objects.get(username=username)
    
    # 1. Verify User role and properties
    assert user.role == expected_role, f"Role mismatch for {username}: expected {expected_role}, got {user.role}"
    print(f"[OK] User: {username:<14} | Role: {user.role:<12}")

    # 2. Verify Django Group membership
    user_groups = list(user.groups.values_list('name', flat=True))
    assert expected_role in user_groups, f"Group mismatch for {username}: {user_groups}"
    print(f"     Group membership verified: {user_groups}")

    # 3. Test user_has_role helper
    assert user_has_role(user, [expected_role]), f"user_has_role failed for {username}"
    print(f"     RBAC user_has_role({expected_role}): PASS")

    # 4. Force login and test dispatch redirect
    client.force_login(user)
    dispatch_res = client.get('/accounts/dispatch/', follow=False)
    assert dispatch_res.status_code == 302, f"Dispatch status {dispatch_res.status_code}"
    assert dispatch_res.url == expected_dashboard, f"Dispatch URL mismatch: {dispatch_res.url} vs {expected_dashboard}"
    print(f"     Dispatch redirect: {dispatch_res.url} [302 FOUND]")

    # 5. Access target dashboard
    dash_res = client.get(expected_dashboard)
    assert dash_res.status_code == 200, f"Dashboard {expected_dashboard} returned {dash_res.status_code}"
    print(f"     Target Dashboard: {expected_dashboard} [HTTP 200 OK]")

print("\n=== ALL 4 PRIMARY ROLES VERIFIED WITH 100% SUCCESS! ===")

