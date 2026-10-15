import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
import django
django.setup()

from django.test import Client
from apps.research.models import StipendDisbursement
from apps.core_admin.models import AdminAuditLog
from apps.academics.models import Enrollment, CourseOffering

client = Client()

print("=" * 60)
print("TESTING END-TO-END BUSINESS WORKFLOWS")
print("=" * 60)

# Workflow 1: Two-Stage Stipend Approval
print("\n[Workflow 1] Testing 2-Stage Stipend Approval & Disbursement:")

# Find a pending stipend
stipend = StipendDisbursement.objects.filter(payment_status='PENDING_PI_APPROVAL').first()
assert stipend is not None, "Expected pending stipend from seed data"
print(f"Initial stipend state: ID={stipend.id}, Junior={stipend.junior.full_name}, Status={stipend.payment_status}")

# Stage 1: PI Dr. Yatendra Sahu logs in and approves
client.login(username='dr_sahu', password='pass123')
res = client.post(f'/faculty-portal/stipend/approve/{stipend.id}/', follow=True)
assert res.status_code == 200
stipend.refresh_from_db()
print(f"After PI Approval: Status={stipend.payment_status}, PI_Approved={stipend.pi_approved}")
assert stipend.pi_approved == True
assert stipend.payment_status == 'APPROVED_BY_PI'
client.logout()

# Stage 2: Office Staff Sunita logs in and disburses
client.login(username='staff_sunita', password='pass123')
res = client.post(
    f'/office-portal/stipend/disburse/{stipend.id}/',
    {'transaction_reference': 'UTR-TEST-12345678'},
    follow=True
)
assert res.status_code == 200
stipend.refresh_from_db()
print(f"After Office Disbursement: Status={stipend.payment_status}, TxRef={stipend.transaction_reference}")
assert stipend.payment_status == 'PROCESSED'
assert stipend.transaction_reference == 'UTR-TEST-12345678'
client.logout()
print("[SUCCESS] 2-Stage Stipend Workflow Verified!")

# Workflow 2: Student Enrollment and Drop
print("\n[Workflow 2] Testing Student Course Enrollment & Drop:")
client.login(username='atharv_pathak', password='pass123')
offering = CourseOffering.objects.exclude(enrollments__student__user__username='atharv_pathak').first()
if offering:
    # Enroll
    res = client.post(f'/student-portal/enroll/{offering.id}/', follow=True)
    assert res.status_code == 200
    enrollment = Enrollment.objects.filter(student__user__username='atharv_pathak', offering=offering).first()
    assert enrollment is not None
    print(f"Enrollment state: {enrollment}")
    # Drop
    res = client.post(f'/student-portal/drop/{enrollment.id}/', follow=True)
    assert res.status_code == 200
    enrollment.refresh_from_db()
    assert enrollment.status == 'DROPPED'
    print("[SUCCESS] Course Enrollment & Drop Verified!")
client.logout()
print("\n[Workflow 3] Testing Admin Safeguards & Immutable Audit Logging:")
client.login(username='admin', password='pass123')

# Test failed challenge match
initial_logs_count = AdminAuditLog.objects.count()
res = client.post(
    '/admin-portal/execute-radical-action/',
    {
        'action_type': 'DROP TABLE',
        'target_entity': 'test_dummy',
        'confirmation_text': 'WRONG TEXT',
        'admin_password': 'admin123',
        'justification_reason': 'Automated test of failure',
    },
    follow=True
)
assert res.status_code == 200
latest_log = AdminAuditLog.objects.order_by('-created_at').first()
print(f"Failed challenge logged as: {latest_log.status}")
assert latest_log.status == 'REJECTED_BAD_CONFIRMATION'

# Test correct challenge match
res = client.post(
    '/admin-portal/execute-radical-action/',
    {
        'action_type': 'DROP TABLE',
        'target_entity': 'test_dummy',
        'confirmation_text': 'DROP TABLE test_dummy',
        'admin_password': 'pass123',
        'justification_reason': 'Automated test of verified safeguard execution',
    },
    follow=True
)
assert res.status_code == 200
latest_log = AdminAuditLog.objects.order_by('-created_at').first()
print(f"Verified challenge executed & logged as: {latest_log.status}")
assert latest_log.status == 'EXECUTED'
client.logout()
print("[SUCCESS] Danger Zone Safeguards & Audit Log Verified!")

print("\n" + "=" * 60)
print("ALL WORKFLOWS EXECUTED AND VERIFIED SUCCESSFULLY!")
print("=" * 60)
