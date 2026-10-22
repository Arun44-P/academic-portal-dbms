"""
Comprehensive Role-Based Access Control (RBAC) Test Suite
Covers 4 Primary Roles: STUDENT, FACULTY, OFFICE_STAFF, ADMIN
Enforces Record-Level Ownership Scoping, HTTP 403 Forbidden Guards,
IDOR Immunity, Server-Side Score Validation, and Last Active Admin Safeguards.
"""
import os
import sys
from pathlib import Path
from decimal import Decimal

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
import django
django.setup()

import unittest
from django.test import Client, RequestFactory
from django.contrib.messages import get_messages
from apps.accounts.models import (
    UserAccount,
    StudentProfile,
    InstructorProfile,
    OfficeStaffProfile,
    AdminProfile
)
from apps.accounts.permissions import user_has_role
from apps.academics.models import (
    CourseOffering,
    Enrollment,
    Assessment,
    StudentMark,
    AttendanceRecord,
    MarksAuditLog,
    StudentFeeAccount
)
from apps.core_admin.models import AdminAuditLog
from apps.core_admin.views import toggle_user_status


class RBACTestSuite(unittest.TestCase):
    def setUp(self):
        self.client = Client()
        self.student_user = UserAccount.objects.get(username='atharv_pathak')
        self.faculty_user = UserAccount.objects.get(username='dr_sahu')
        self.other_faculty = UserAccount.objects.get(username='dr_chaurasia')
        self.office_user = UserAccount.objects.get(username='staff_sunita')
        self.admin_user = UserAccount.objects.get(username='admin')

    # ========================================================================
    # 1. PRIMARY ROLE & GROUP MEMBERSHIP VERIFICATION
    # ========================================================================
    def test_01_primary_role_definitions_and_groups(self):
        """Verify all accounts hold exactly one standardized business role and matching group."""
        roles = [
            (self.student_user, 'STUDENT', '/student-portal/dashboard/'),
            (self.faculty_user, 'FACULTY', '/faculty-portal/dashboard/'),
            (self.office_user, 'OFFICE_STAFF', '/office-portal/dashboard/'),
            (self.admin_user, 'ADMIN', '/admin-portal/dashboard/'),
        ]
        for user, expected_role, expected_dash in roles:
            with self.subTest(role=expected_role):
                self.assertEqual(user.role, expected_role)
                user_groups = list(user.groups.values_list('name', flat=True))
                self.assertIn(expected_role, user_groups)
                self.assertTrue(user_has_role(user, [expected_role]))

                # Dispatch test
                self.client.force_login(user)
                res = self.client.get('/accounts/dispatch/', follow=False)
                self.assertEqual(res.status_code, 302)
                self.assertEqual(res.url, expected_dash)
                self.client.logout()

    # ========================================================================
    # 2. STUDENT PERMISSIONS & CONFIDENTIALITY
    # ========================================================================
    def test_02_student_authorized_access(self):
        """Student accesses self-scoped dashboards, attendance, and fee status."""
        self.client.force_login(self.student_user)

        res_dash = self.client.get('/student-portal/dashboard/')
        self.assertEqual(res_dash.status_code, 200)

        res_grades = self.client.get('/student-portal/attendance-grades/')
        self.assertEqual(res_grades.status_code, 200)
        content = res_grades.content.decode()

        # Published marks are visible
        self.assertIn('Mid-Term Exam', content)
        # Draft marks are strictly confidential and MUST NOT appear
        self.assertNotIn('Draft Quiz 1', content)

        res_courses = self.client.get('/student-portal/courses/')
        self.assertEqual(res_courses.status_code, 200)

        res_fee = self.client.get('/student-portal/fee-status/')
        self.assertEqual(res_fee.status_code, 200)
        self.client.logout()

    def test_03_student_forbidden_boundaries(self):
        """Student is blocked with HTTP 403 Forbidden from Faculty, Office, and Admin portals."""
        self.client.force_login(self.student_user)

        forbidden_urls = [
            '/faculty-portal/dashboard/',
            '/faculty-portal/attendance/',
            '/faculty-portal/marks/',
            '/office-portal/dashboard/',
            '/office-portal/students/',
            '/office-portal/faculty/',
            '/admin-portal/dashboard/',
            '/admin-portal/console/',
            '/admin-portal/users/',
            '/admin-portal/audit-logs/',
        ]
        for url in forbidden_urls:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 403, f"Student was not blocked with 403 on {url}")

        self.client.logout()

    # ========================================================================
    # 3. FACULTY PERMISSIONS, IDOR IMMUNITY & SCORE VALIDATION
    # ========================================================================
    def test_04_faculty_authorized_access(self):
        """Faculty accesses teaching dashboard, assigned sections, attendance and marks entry."""
        self.client.force_login(self.faculty_user)

        res_dash = self.client.get('/faculty-portal/dashboard/')
        self.assertEqual(res_dash.status_code, 200)

        res_sections = self.client.get('/faculty-portal/sections/')
        self.assertEqual(res_sections.status_code, 200)

        res_att = self.client.get('/faculty-portal/attendance/')
        self.assertEqual(res_att.status_code, 200)

        res_marks = self.client.get('/faculty-portal/marks/')
        self.assertEqual(res_marks.status_code, 200)

        self.client.logout()

    def test_05_faculty_idor_protection(self):
        """Faculty attempting to access another instructor's course section is blocked with HTTP 403."""
        self.client.force_login(self.faculty_user)

        # dr_sahu owns Offering 1 & 4. Offering 2 is owned by dr_chaurasia.
        res_att_idor = self.client.get('/faculty-portal/attendance/?offering_id=2')
        self.assertEqual(res_att_idor.status_code, 403, "IDOR attendance was not blocked with 403")

        res_marks_idor = self.client.get('/faculty-portal/marks/?offering_id=2')
        self.assertEqual(res_marks_idor.status_code, 403, "IDOR marks entry was not blocked with 403")

        self.client.logout()

    def test_06_faculty_server_score_validation(self):
        """Server-side maximum score validation rejects scores exceeding max_marks."""
        self.client.force_login(self.faculty_user)
        offering1 = CourseOffering.objects.get(id=1)
        ass = Assessment.objects.filter(offering=offering1).first()
        enr = Enrollment.objects.filter(offering=offering1, status='ENROLLED').first()

        # Post exceeding score
        excess_score = ass.max_marks + Decimal('50.00')
        post_data = {
            'offering_id': 1,
            'save_draft': 'true',
            f'mark_{enr.student.roll_number}_{ass.id}': str(excess_score),
        }
        res = self.client.post('/faculty-portal/marks/', post_data, follow=True)
        messages = [m.message for m in get_messages(res.wsgi_request)]
        self.assertTrue(any('exceeds maximum allowed score' in m for m in messages))

        self.client.logout()

    def test_07_marks_audit_logging(self):
        """Editing an existing student mark writes an immutable record to MarksAuditLog."""
        self.client.force_login(self.faculty_user)
        offering1 = CourseOffering.objects.get(id=1)
        ass = Assessment.objects.filter(offering=offering1).first()
        enr = Enrollment.objects.filter(offering=offering1, status='ENROLLED').first()

        initial_audit_count = MarksAuditLog.objects.count()

        # Save a score
        valid_score = Decimal('19.00')
        post_data = {
            'offering_id': 1,
            'save_draft': 'true',
            f'mark_{enr.student.roll_number}_{ass.id}': str(valid_score),
            'change_reason': 'Automated RBAC verification test',
        }
        res = self.client.post('/faculty-portal/marks/', post_data, follow=True)
        self.assertEqual(res.status_code, 200)

        # Update score to trigger audit log
        updated_score = Decimal('20.00')
        post_data[f'mark_{enr.student.roll_number}_{ass.id}'] = str(updated_score)
        res2 = self.client.post('/faculty-portal/marks/', post_data, follow=True)
        self.assertEqual(res2.status_code, 200)

        latest_log = MarksAuditLog.objects.first()
        self.assertIsNotNone(latest_log)
        self.assertEqual(latest_log.modified_by, self.faculty_user)
        self.assertEqual(latest_log.new_score, updated_score)

        self.client.logout()

    # ========================================================================
    # 4. OFFICE STAFF PERMISSIONS & READ-ONLY ACCESS
    # ========================================================================
    def test_08_office_staff_authorized_access(self):
        """Office staff accesses fee management and read-only student/faculty directories."""
        self.client.force_login(self.office_user)

        res_fee = self.client.get('/office-portal/dashboard/')
        self.assertEqual(res_fee.status_code, 200)

        res_students = self.client.get('/office-portal/students/')
        self.assertEqual(res_students.status_code, 200)
        self.assertIn('Atharv Pathak', res_students.content.decode())

        res_faculty = self.client.get('/office-portal/faculty/')
        self.assertEqual(res_faculty.status_code, 200)
        self.assertIn('Yatendra Sahu', res_faculty.content.decode())

        self.client.logout()

    def test_09_office_staff_forbidden_boundaries(self):
        """Office staff is strictly blocked from faculty evaluation and admin consoles."""
        self.client.force_login(self.office_user)

        forbidden_urls = [
            '/faculty-portal/attendance/',
            '/faculty-portal/marks/',
            '/admin-portal/dashboard/',
            '/admin-portal/console/',
            '/admin-portal/users/',
            '/admin-portal/audit-logs/',
        ]
        for url in forbidden_urls:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 403, f"Office staff was not blocked with 403 on {url}")

        self.client.logout()

    # ========================================================================
    # 5. ADMINISTRATOR GOVERNANCE & LAST ADMIN SAFEGUARD
    # ========================================================================
    def test_10_admin_authorized_access(self):
        """Administrator accesses institute overview, database console, users, and audit logs."""
        self.client.force_login(self.admin_user)

        for url in ['/admin-portal/dashboard/', '/admin-portal/console/', '/admin-portal/users/', '/admin-portal/audit-logs/']:
            with self.subTest(url=url):
                res = self.client.get(url)
                self.assertEqual(res.status_code, 200)

        self.client.logout()

    def test_11_last_administrator_safeguard(self):
        """Safeguard guarantees that the last active institutional administrator cannot be deactivated."""
        self.client.force_login(self.admin_user)

        # 1. Self deactivation test
        res_self = self.client.get(f'/admin-portal/users/{self.admin_user.id}/toggle/', follow=True)
        msgs = [m.message for m in get_messages(res_self.wsgi_request)]
        self.assertTrue(any('Cannot deactivate your own administrator account' in m for m in msgs))

        # 2. Last active admin deactivation safeguard test via request simulation
        factory = RequestFactory()
        req = factory.get(f'/admin-portal/users/{self.admin_user.id}/toggle/')
        # Create a mock temporary admin
        temp_admin = UserAccount.objects.create(
            username='temp_admin_verifier',
            email='temp_admin@college.edu',
            role='ADMIN',
            is_active=False
        )
        req.user = temp_admin
        from django.contrib.messages.storage.fallback import FallbackStorage
        setattr(req, 'session', 'session')
        setattr(req, '_messages', FallbackStorage(req))

        toggle_user_status(req, self.admin_user.id)
        self.admin_user.refresh_from_db()
        self.assertTrue(self.admin_user.is_active, "Last active admin was improperly deactivated!")

        temp_admin.delete()
        self.client.logout()

    def test_12_admin_user_provisioning(self):
        """Administrator successfully provisions a new student with group membership and fee ledger."""
        self.client.force_login(self.admin_user)
        uname = 'rbac_test_student_user'
        UserAccount.objects.filter(username=uname).delete()

        post_data = {
            'username': uname,
            'email': 'rbac_test@college.edu',
            'full_name': 'Meera Rajput',
            'password': 'TempPassword#2026',
            'role': 'STUDENT',
            'roll_number': '2026CS888',
            'current_semester': '2',
        }
        res = self.client.post('/admin-portal/users/', post_data, follow=True)
        self.assertEqual(res.status_code, 200)

        new_user = UserAccount.objects.filter(username=uname).first()
        self.assertIsNotNone(new_user)
        self.assertEqual(new_user.role, 'STUDENT')
        self.assertTrue(new_user.groups.filter(name='STUDENT').exists())
        self.assertIsNotNone(new_user.student_profile)
        self.assertTrue(StudentFeeAccount.objects.filter(student=new_user.student_profile).exists())

        new_user.delete()
        self.client.logout()


if __name__ == '__main__':
    unittest.main()

