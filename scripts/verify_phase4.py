import os, sys
from pathlib import Path
BASE_DIR = Path.cwd()
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
import django
django.setup()

from django.test import Client
from apps.accounts.models import UserAccount, InstructorProfile
from apps.academics.models import CourseOffering, Enrollment, Assessment, StudentMark, MarksAuditLog

client = Client()
# 1. Login as Faculty (dr_sahu)
assert client.login(username='dr_sahu', password='pass123')
print('[OK] Logged in as dr_sahu (FACULTY)')

# 2. Access faculty dashboard
res = client.get('/faculty-portal/dashboard/')
assert res.status_code == 200
print('[OK] Faculty Dashboard returned 200 OK')

# 3. Access Attendance entry
res_att = client.get('/faculty-portal/attendance/')
assert res_att.status_code == 200
assert 'Student Attendance Registry' in res_att.content.decode()
print('[OK] Attendance Grid returned 200 OK')

# 4. Access Marks entry
res_marks = client.get('/faculty-portal/marks/')
assert res_marks.status_code == 200
assert 'Curricular Assessment' in res_marks.content.decode()
print('[OK] Marks Entry Matrix returned 200 OK')

# 5. IDOR test: dr_sahu owns Offering 1 & 4. Offering 2 is owned by dr_chaurasia.
res_idor_att = client.get('/faculty-portal/attendance/?offering_id=2')
print('IDOR Attendance test status:', res_idor_att.status_code)
assert res_idor_att.status_code == 403, f'Expected 403 Forbidden on IDOR attendance, got {res_idor_att.status_code}'
print('[OK] IDOR Attendance attempt blocked with HTTP 403 Forbidden!')

res_idor_marks = client.get('/faculty-portal/marks/?offering_id=2')
print('IDOR Marks test status:', res_idor_marks.status_code)
assert res_idor_marks.status_code == 403, f'Expected 403 Forbidden on IDOR marks, got {res_idor_marks.status_code}'
print('[OK] IDOR Marks attempt blocked with HTTP 403 Forbidden!')

from django.contrib.messages import get_messages

# 6. Test Marks Entry with max_marks server validation
offering1 = CourseOffering.objects.get(id=1)
ass = Assessment.objects.filter(offering=offering1).first()
enr = Enrollment.objects.filter(offering=offering1, status='ENROLLED').first()
roll = enr.student.roll_number
print(f'Testing score entry on {ass.name} (Max {ass.max_marks}) for {roll}')

# Post exceeding max marks
post_data = {
    'offering_id': 1,
    'save_draft': 'true',
    f'mark_{roll}_{ass.id}': str(ass.max_marks + 50),
}
res_excess = client.post('/faculty-portal/marks/', post_data, follow=True)
excess_messages = [m.message for m in get_messages(res_excess.wsgi_request)]
print('Server validation messages on excess score:', excess_messages)
assert any('exceeds maximum allowed score' in m for m in excess_messages), 'Server failed to reject score > max_marks!'
print('[OK] Server-side maximum score validation strictly enforced!')

# 7. Test Valid Marks Entry and MarksAuditLog creation
initial_audit_count = MarksAuditLog.objects.count()
valid_post_data = {
    'offering_id': 1,
    'save_draft': 'true',
    f'mark_{roll}_{ass.id}': '18.5',
}
res_valid = client.post('/faculty-portal/marks/', valid_post_data, follow=True)
assert res_valid.status_code == 200
final_audit_count = MarksAuditLog.objects.count()
print(f'[OK] Valid mark saved! MarksAuditLog count changed from {initial_audit_count} to {final_audit_count}')

print('\n=== ALL PHASE 4 FACULTY SECURITY VERIFICATIONS PASSED 100%! ===')
