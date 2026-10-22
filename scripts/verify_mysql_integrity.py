import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import django
import sqlite3
import pymysql
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
django.setup()

from django.contrib.auth import authenticate
from apps.accounts.models import UserAccount, StudentProfile, InstructorProfile, OfficeStaffProfile, AdminProfile
from apps.academics.models import Course, Enrollment, StudentFeeAccount, FeePayment

print("=" * 70)
print("PHASE 6: DATA INTEGRITY & MODEL RELATIONSHIP VERIFICATION (MYSQL)")
print("=" * 70)

# 1. Total Table count
from django.db import connection
with connection.cursor() as cur:
    cur.execute("SHOW TABLES;")
    mysql_tables = [r[0] for r in cur.fetchall()]
print(f"1. MySQL Total Tables: {len(mysql_tables)} (Expected: 31)")
assert len(mysql_tables) == 31

# 2. Record counts & Primary Keys
users = UserAccount.objects.all().order_by('id')
print(f"2. User Accounts in MySQL: {users.count()} (Expected: 8)")
assert users.count() == 8

# 3. Usernames, Emails, Roles & Password Hashes
print("3. Testing Password Hash Authentication on MySQL:")
test_users = [
    ('admin', 'pass123', 'ADMIN'),
    ('dr_sahu', 'pass123', 'TEACHER'),
    ('dr_chaurasia', 'pass123', 'TEACHER'),
    ('prof_neha', 'pass123', 'TEACHER'),
    ('staff_sunita', 'pass123', 'OFFICE_STAFF'),
    ('atharv_pathak', 'pass123', 'STUDENT'),
    ('arun_patidar', 'pass123', 'STUDENT'),
    ('prashast_mathur', 'pass123', 'STUDENT'),
]
for username, pwd, role in test_users:
    user = authenticate(username=username, password=pwd)
    assert user is not None, f"Auth failed for {username}!"
    assert user.role == role, f"Role mismatch for {username}!"
    print(f"   [PASS] {username:<16} | Role: {user.role:<12} | Auth: OK")

# 4. Student-to-User & Program Relationships
print("\n4. Testing Student Profiles & Relationships:")
students = StudentProfile.objects.select_related('user', 'program__department').order_by('roll_number')
assert students.count() == 3
for s in students:
    assert s.user.username in ['atharv_pathak', 'arun_patidar', 'prashast_mathur']
    assert s.program.department.code == 'CSE'
    print(f"   [PASS] Roll: {s.roll_number} | Name: {s.user.get_full_name()} | Program: {s.program.name}")

# 5. Faculty-to-User & Department Relationships
print("\n5. Testing Faculty Profiles & Relationships:")
instructors = InstructorProfile.objects.select_related('user', 'department').order_by('employee_code')
assert instructors.count() == 3
for i in instructors:
    print(f"   [PASS] Code: {i.employee_code} | Name: {i.user.get_full_name()} | Dept: {i.department.code}")

# 6. Course & Enrollment Relationships
print("\n6. Testing Courses & Enrollments:")
courses = Course.objects.all()
enrollments = Enrollment.objects.all()
print(f"   [PASS] Courses count: {courses.count()} (Expected: 8)")
print(f"   [PASS] Active Enrollments count: {enrollments.count()} (Expected: 14)")
assert courses.count() == 8
assert enrollments.count() == 14

# 7. Fee Account Balances & Precision
print("\n7. Testing Fee Account Balances (Decimal Precision):")
fee_accounts = StudentFeeAccount.objects.select_related('student__user').order_by('student__roll_number')
assert fee_accounts.count() == 3

expected_balances = {
    '2024BCS001': (Decimal('300000.00'), Decimal('200000.00'), Decimal('100000.00'), 'PARTIAL'),
    '2024BCS002': (Decimal('300000.00'), Decimal('300000.00'), Decimal('0.00'), 'PAID'),
    '2024BCS003': (Decimal('300000.00'), Decimal('50000.00'), Decimal('250000.00'), 'OVERDUE'),
}

for fa in fee_accounts:
    fa.recalculate_status()
    exp_tot, exp_paid, exp_rem, exp_st = expected_balances[fa.student.roll_number]
    assert fa.total_fee == exp_tot, f"Total fee mismatch on {fa.student.roll_number}"
    assert fa.total_paid == exp_paid, f"Paid fee mismatch on {fa.student.roll_number}"
    assert fa.remaining_fee == exp_rem, f"Remaining fee mismatch on {fa.student.roll_number}"
    assert fa.status == exp_st, f"Status mismatch on {fa.student.roll_number}"
    print(f"   [PASS] {fa.student.roll_number}: Total Rs.{fa.total_fee} | Paid Rs.{fa.total_paid} | Rem Rs.{fa.remaining_fee} | Status: {fa.status}")

# 8. Fee Payments & References
print("\n8. Testing Fee Payment Receipts & References:")
payments = FeePayment.objects.select_related('fee_account__student').order_by('receipt_number')
assert payments.count() == 3
for p in payments:
    print(f"   [PASS] Receipt: {p.receipt_number} | Ref: {p.transaction_reference} | Amount: Rs.{p.amount} | Method: {p.payment_method}")

print("\n" + "=" * 70)
print("ALL DATA INTEGRITY CHECKS PASSED ON MYSQL!")
print("=" * 70)
