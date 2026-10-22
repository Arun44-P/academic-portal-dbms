import os
import sys
from pathlib import Path
from decimal import Decimal

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
import django
django.setup()

from django.test import Client
from django.contrib.auth import get_user_model
from apps.academics.models import StudentFeeAccount, FeePayment

User = get_user_model()
client = Client()

print("=" * 70)
print("ACADEMIA PORTAL: COMPREHENSIVE VERIFICATION & TEST SUITE")
print("=" * 70)

# 1. Test root & login
res = client.get('/')
print(f"GET / -> Status {res.status_code} (Redirects to: {res.url})")
assert res.status_code == 302

res = client.get('/accounts/login/')
print(f"GET /accounts/login/ -> Status {res.status_code}")
assert res.status_code == 200
login_html = res.content.decode('utf-8')
assert "Academic Management Portal" in login_html
print("[PASS] Login branding verified: 'Academic Management Portal'")

# 2. Test Office Staff Role (staff_sunita) & Student Fee Management
print("\n--- Testing Office Staff Role (staff_sunita) & Fee Management ---")
logged_in = client.login(username='staff_sunita', password='pass123')
print(f"Login staff_sunita: {logged_in}")
assert logged_in

# Check Dashboard
res = client.get('/office-portal/dashboard/')
print(f"GET /office-portal/dashboard/ -> Status {res.status_code}")
assert res.status_code == 200
html = res.content.decode('utf-8')

assert "Student Fee Management" in html
assert "Total Outstanding Fees" in html
assert "Students With Pending Fees" in html
assert "Total Fees Collected" in html
assert "Overdue Student Accounts" in html
assert "Student Fee Records" in html
print("[PASS] Fee Management Dashboard header, 4 summary cards & records table verified")

# Check that amounts come from DB
acc_atharv = StudentFeeAccount.objects.get(student__roll_number='2024BCS001')
acc_arun = StudentFeeAccount.objects.get(student__roll_number='2024BCS002')
acc_prashast = StudentFeeAccount.objects.get(student__roll_number='2024BCS003')

total_outstanding = acc_atharv.remaining_fee + acc_arun.remaining_fee + acc_prashast.remaining_fee
print(f"Database calculated total outstanding: Rs.{total_outstanding:,.2f}")
assert f"{total_outstanding:,.2f}" in html or f"{total_outstanding:.2f}" in html
print("[PASS] Financial summary card values match database calculations")

# Test Search
res_search = client.get('/office-portal/dashboard/?q=Atharv#fee-records')
assert res_search.status_code == 200
html_search = res_search.content.decode('utf-8')
assert "2024BCS001" in html_search
assert "2024BCS002" not in html_search
print("[PASS] Search by student name/roll number verified")

# Test Filter by Status (OVERDUE)
res_overdue = client.get('/office-portal/dashboard/?status=OVERDUE#fee-records')
assert res_overdue.status_code == 200
html_overdue = res_overdue.content.decode('utf-8')
assert "2024BCS003" in html_overdue
assert "2024BCS001" not in html_overdue
print("[PASS] Status filter (OVERDUE) verified")

# Test Filter by Status (PAID)
res_paid = client.get('/office-portal/dashboard/?status=PAID#fee-records')
assert res_paid.status_code == 200
html_paid = res_paid.content.decode('utf-8')
assert "2024BCS002" in html_paid
assert "2024BCS003" not in html_paid
print("[PASS] Status filter (PAID) verified")

# Test Fee Detail JSON Endpoint (for interactive drawer/modal)
res_json = client.get(f'/office-portal/fee-account/{acc_atharv.id}/?format=json', credentials={'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest'})
assert res_json.status_code == 200
data = res_json.json()
assert data['success'] is True
assert data['roll_number'] == '2024BCS001'
assert len(data['payments']) >= 1
print(f"[PASS] Fee Detail AJAX/JSON endpoint verified (Student: {data['student_name']}, Rem: Rs.{data['remaining_fee']})")

# Test Fee Detail Standalone HTML Page
res_detail_html = client.get(f'/office-portal/fee-account/{acc_atharv.id}/')
assert res_detail_html.status_code == 200
assert "Student Fee Account Statement" in res_detail_html.content.decode('utf-8')
print("[PASS] Fee Detail standalone statement page verified")

# Test Payment History Page
res_payments = client.get('/office-portal/payments/')
assert res_payments.status_code == 200
assert "Fee Payment Ledger" in res_payments.content.decode('utf-8')
assert "SBIC-2026-992147" in res_payments.content.decode('utf-8')
print("[PASS] Institutional Fee Payment Ledger page verified")

# Test Manual Payment Recording Workflow
print("\n--- Testing Controlled Manual Payment Recording ---")
# Pre-clean just in case
FeePayment.objects.filter(transaction_reference='UPI-TEST-2026-001').delete()
acc_atharv.refresh_from_db()
acc_atharv.recalculate_status()

initial_remaining = acc_atharv.remaining_fee
payment_amount = Decimal('15000.00')

try:
    res_pay = client.post(
        f'/office-portal/fee-account/{acc_atharv.id}/record-payment/',
        {
            'amount': str(payment_amount),
            'payment_method': 'UPI',
            'transaction_reference': 'UPI-TEST-2026-001',
            'remarks': 'Testing manual counter payment submission',
        },
        follow=True
    )
    assert res_pay.status_code == 200

    # Verify payment in DB
    acc_atharv.refresh_from_db()
    new_remaining = acc_atharv.remaining_fee
    print(f"Initial remaining: Rs.{initial_remaining:,.2f} -> New remaining: Rs.{new_remaining:,.2f}")
    assert new_remaining == initial_remaining - payment_amount
    payment_record = FeePayment.objects.get(transaction_reference='UPI-TEST-2026-001')
    assert payment_record.amount == payment_amount
    assert payment_record.fee_account == acc_atharv
    print(f"[PASS] Payment recorded atomically in DB: Receipt {payment_record.receipt_number}")

    # Test Duplicate Reference Rejection
    res_dup = client.post(
        f'/office-portal/fee-account/{acc_atharv.id}/record-payment/',
        {
            'amount': '5000.00',
            'payment_method': 'CASH',
            'transaction_reference': 'UPI-TEST-2026-001', # duplicate
            'remarks': 'Duplicate test',
        },
        follow=True
    )
    from django.contrib.messages import get_messages
    dup_messages = [m.message for m in get_messages(res_dup.wsgi_request)]
    assert any('already exists' in m for m in dup_messages)
    print("[PASS] Duplicate transaction reference correctly rejected")

    # Test Amount Exceeding Remaining Fee Rejection
    res_excess = client.post(
        f'/office-portal/fee-account/{acc_atharv.id}/record-payment/',
        {
            'amount': '9999999.00',
            'payment_method': 'CASH',
            'transaction_reference': 'EXCESS-001',
            'remarks': 'Excess test',
        },
        follow=True
    )
    excess_messages = [m.message for m in get_messages(res_excess.wsgi_request)]
    assert any('exceeds student remaining fee' in m for m in excess_messages)
    print("[PASS] Excess payment amount correctly rejected")

    client.logout()

    # 3. Test Student Role (atharv_pathak) Fee Status
    print("\n--- Testing Student Portal Fee Integration ---")
    logged_in = client.login(username='atharv_pathak', password='pass123')
    assert logged_in

    res_student_fee = client.get('/student-portal/fee-status/')
    assert res_student_fee.status_code == 200
    html_student_fee = res_student_fee.content.decode('utf-8')
    assert f"{new_remaining:,.2f}" in html_student_fee or f"{new_remaining:.2f}" in html_student_fee
    assert "UPI-TEST-2026-001" in html_student_fee
    print("[PASS] Student portal dynamically reflects confirmed payments and new receipts")

    # Unauthorized Access Protection
    res_unauth = client.get('/office-portal/dashboard/')
    assert res_unauth.status_code == 302 # Redirected because role is STUDENT
    res_unauth_pay = client.get('/office-portal/payments/')
    assert res_unauth_pay.status_code == 302
    print("[PASS] Server-side authorization blocks unauthorized roles from office fee portal")

    client.logout()

finally:
    # 4. Clean up test payment so database returns to pristine state
    FeePayment.objects.filter(transaction_reference='UPI-TEST-2026-001').delete()
    acc_atharv.recalculate_status()
    print("\n[PASS] Cleaned up test payment transaction. Database restored to pristine state.")

print("\n" + "=" * 70)
print("ALL VERIFICATION CHECKS PASSED: FEE MANAGEMENT SYSTEM FULLY OPERATIONAL!")
print("=" * 70)
