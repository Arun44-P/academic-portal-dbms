"""
Seed initial realistic attendance and assessment marks records into MySQL.
"""
import os
import sys
import datetime
from decimal import Decimal
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'academic_portal.settings')
import django
django.setup()

from apps.accounts.models import StudentProfile, InstructorProfile
from apps.academics.models import (
    CourseOffering, Enrollment, Assessment, StudentMark, AttendanceRecord
)

print("=== Seeding Initial Academic Assessments & Attendance Records ===")

offerings = CourseOffering.objects.all().select_related('course', 'instructor')

# 1. Create Assessments for each active offering
for off in offerings:
    # Assessment 1: Mid-Term Examination (Published)
    mid_term, _ = Assessment.objects.get_or_create(
        offering=off,
        name="Mid-Term Examination",
        defaults={
            'assessment_type': 'MID_TERM',
            'max_marks': Decimal('50.00'),
            'weightage_percent': Decimal('30.00'),
            'is_published': True,
            'created_by': off.instructor,
        }
    )

    # Assessment 2: Continuous Class Quiz 1 (Published)
    quiz, _ = Assessment.objects.get_or_create(
        offering=off,
        name="Continuous Class Quiz 1",
        defaults={
            'assessment_type': 'QUIZ',
            'max_marks': Decimal('20.00'),
            'weightage_percent': Decimal('10.00'),
            'is_published': True,
            'created_by': off.instructor,
        }
    )

    # Assessment 3: End-Term Examination (Draft / Unpublished)
    end_term, _ = Assessment.objects.get_or_create(
        offering=off,
        name="End-Term Examination",
        defaults={
            'assessment_type': 'END_TERM',
            'max_marks': Decimal('100.00'),
            'weightage_percent': Decimal('50.00'),
            'is_published': False,  # DRAFT - visible only to faculty
            'created_by': off.instructor,
        }
    )

    # 2. Add StudentMark for all enrolled students
    enrollments = Enrollment.objects.filter(offering=off, status='ENROLLED')
    for enr in enrollments:
        roll = enr.student.roll_number
        if '001' in roll:
            mid_score, quiz_score = Decimal('44.00'), Decimal('18.50')
        elif '002' in roll:
            mid_score, quiz_score = Decimal('39.50'), Decimal('16.00')
        else:
            mid_score, quiz_score = Decimal('46.00'), Decimal('19.00')

        # Mid-Term Mark
        StudentMark.objects.get_or_create(
            assessment=mid_term,
            enrollment=enr,
            defaults={
                'marks_obtained': mid_score,
                'is_absent': False,
                'remarks': 'Good conceptual clarity',
                'entered_by': off.instructor,
            }
        )

        # Quiz Mark
        StudentMark.objects.get_or_create(
            assessment=quiz,
            enrollment=enr,
            defaults={
                'marks_obtained': quiz_score,
                'is_absent': False,
                'remarks': 'Solved on time',
                'entered_by': off.instructor,
            }
        )

    # 3. Create Attendance sessions (12 lecture sessions)
    base_date = datetime.date(2026, 9, 1)
    for session_idx in range(12):
        session_date = base_date + datetime.timedelta(days=session_idx * 3)
        topic = f"{off.course.course_code} Session #{session_idx + 1}: Module Topics"

        for enr in enrollments:
            roll = enr.student.roll_number
            # Realistic attendance distribution (majority present, occasional absence)
            if '002' in roll and session_idx in (2, 7):
                status = 'ABSENT'
            elif '003' in roll and session_idx == 4:
                status = 'ABSENT'
            else:
                status = 'PRESENT'

            AttendanceRecord.objects.get_or_create(
                offering=off,
                student=enr.student,
                session_date=session_date,
                defaults={
                    'status': status,
                    'topic_covered': topic,
                    'marked_by': off.instructor,
                }
            )

print(f"[SUCCESS] Assessments created: {Assessment.objects.count()}")
print(f"[SUCCESS] Student marks entered: {StudentMark.objects.count()}")
print(f"[SUCCESS] Attendance records logged: {AttendanceRecord.objects.count()}")
print("=== Academic Seeding Complete ===")

