import os, sys
from pathlib import Path
BASE_DIR = Path.cwd()
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
import django
django.setup()

from django.test import Client
from django.contrib.messages import get_messages
from apps.accounts.models import UserAccount, StudentProfile
from apps.academics.models import StudentFeeAccount
from apps.core_admin.models import AdminAuditLog

client = Client()
# 1. Login as Admin
assert client.login(username='admin', password='pass123')
print('[OK] Logged in as administrator (admin)')

# 2. Access Admin Dashboard
res_dash = client.get('/admin-portal/dashboard/')
assert res_dash.status_code == 200, f'Expected 200, got {res_dash.status_code}'
print('[OK] Admin Dashboard returned 200 OK')

# 3. Access Database Console
res_console = client.get('/admin-portal/console/')
assert res_console.status_code == 200, f'Expected 200, got {res_console.status_code}'
print('[OK] Admin Database Console returned 200 OK')

# 4. Access Users Directory
res_users = client.get('/admin-portal/users/')
assert res_users.status_code == 200, f'Expected 200, got {res_users.status_code}'
print('[OK] Admin Users Directory returned 200 OK')

# 5. Access Audit Logs
res_logs = client.get('/admin-portal/audit-logs/')
assert res_logs.status_code == 200, f'Expected 200, got {res_logs.status_code}'
print('[OK] Admin Audit Logs returned 200 OK')

# 6. Test Last Administrator Deactivation Safeguard
admin_user = UserAccount.objects.get(username='admin')
# Test self deactivation attempt
res_self = client.get(f'/admin-portal/users/{admin_user.id}/toggle/', follow=True)
msgs = [m.message for m in get_messages(res_self.wsgi_request)]
print('Self deactivation messages:', msgs)
assert any('Cannot deactivate your own administrator account' in m for m in msgs)
print('[OK] Self administrator deactivation blocked!')

# Now test last admin safeguard explicitly by creating a second temporary admin, logging in as second admin, and trying to deactivate the only other admin if count is 1
admin2, created = UserAccount.objects.get_or_create(
    username='admin_temp_safeguard',
    defaults={'email': 'admin2@test.com', 'role': 'ADMIN', 'is_active': False}
)
# admin is the only active admin. Let's try to deactivate admin via toggle_user_status directly when logged in as admin2 (if admin2 was active)
admin2.is_active = True
admin2.set_password('pass123')
admin2.save()

# Login as admin2
client2 = Client()
client2.login(username='admin_temp_safeguard', password='pass123')

# Now there are 2 active admins: admin and admin_temp_safeguard. Deactivate admin_temp_safeguard so only 1 remains
admin2.is_active = False
admin2.save()

# Now admin is the ONLY active admin. Attempting to deactivate admin must be blocked by the last admin safeguard:
# (Simulate request to toggle_user_status)
from django.test import RequestFactory
from apps.core_admin.views import toggle_user_status
factory = RequestFactory()
req = factory.get(f'/admin-portal/users/{admin_user.id}/toggle/')
# Create a dummy superuser/admin request with user = admin2
req.user = admin2
from django.contrib.messages.storage.fallback import FallbackStorage
setattr(req, 'session', 'session')
messages_storage = FallbackStorage(req)
setattr(req, '_messages', messages_storage)

resp = toggle_user_status(req, admin_user.id)
assert admin_user.is_active == True, "Last active admin was deactivated!"
admin_user.refresh_from_db()
assert admin_user.is_active == True, "Last active admin was deactivated in database!"
print('[OK] Security Safeguard: Last active administrator CANNOT be deactivated!')

# Clean up temporary admin
admin2.delete()

# 7. Test Provisioning New User via Admin POST
test_uname = 'new_student_test99'
UserAccount.objects.filter(username=test_uname).delete()

post_payload = {
    'username': test_uname,
    'email': 'new_student_test99@college.edu',
    'full_name': 'Kavya Verma',
    'password': 'TempPassword#2026',
    'role': 'STUDENT',
    'roll_number': '2026CS999',
    'current_semester': '4',
}
res_prov = client.post('/admin-portal/users/', post_payload, follow=True)
assert res_prov.status_code == 200
new_stud = UserAccount.objects.filter(username=test_uname).first()
assert new_stud is not None, "Failed to provision user!"
assert new_stud.role == 'STUDENT', f"Role mismatch: {new_stud.role}"
assert new_stud.student_profile is not None, "Student profile not created!"
assert new_stud.student_profile.roll_number == '2026CS999'
assert StudentFeeAccount.objects.filter(student=new_stud.student_profile).exists(), "Fee account not initialized!"
print(f'[OK] Successfully provisioned new user @{test_uname} with StudentProfile and FeeAccount!')

# Clean up test user
new_stud.delete()

print('\n=== ALL PHASE 6 & 7 ADMINISTRATOR GOVERNANCE VERIFICATIONS PASSED 100%! ===')
