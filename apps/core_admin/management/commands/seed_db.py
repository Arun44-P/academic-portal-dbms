import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction

from apps.accounts.models import (
    AdminProfile,
    OfficeStaffProfile,
    InstructorProfile,
    PermanentFaculty,
    AssistantProfessor,
    VisitingProfessor,
    StudentProfile,
)
from apps.academics.models import (
    Department,
    Program,
    Course,
    AcademicSemester,
    CourseOffering,
    Enrollment,
)
from apps.research.models import (
    ResearchProject,
    ProjectCoInvestigator,
    ResearchJunior,
    StipendDisbursement,
    ResearchPublication,
)

User = get_user_model()


class Command(BaseCommand):
    help = "Seeds database with realistic college academic and research wing data."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Starting database seeding...")

        # 1. Departments
        cse, _ = Department.objects.get_or_create(
            code="CSE",
            defaults={"name": "Computer Science & Engineering", "established_year": 1995},
        )
        ece, _ = Department.objects.get_or_create(
            code="ECE",
            defaults={"name": "Electronics & Communication Engineering", "established_year": 1998},
        )

        # 2. Programs
        btech_cse, _ = Program.objects.get_or_create(
            department=cse,
            name="B.Tech Computer Science",
            defaults={
                "degree_level": "UNDERGRADUATE",
                "duration_years": 4,
                "total_semesters": 8,
            },
        )

        # 3. Academic Semester
        current_sem, _ = AcademicSemester.objects.get_or_create(
            term="FALL",
            academic_year="2026-2027",
            defaults={
                "start_date": datetime.date(2026, 8, 1),
                "end_date": datetime.date(2026, 12, 15),
                "is_current": True,
            },
        )

        # 4. Courses
        cs101, _ = Course.objects.get_or_create(
            course_code="CS301",
            defaults={
                "title": "Database Management Systems",
                "credits": 4,
                "lecture_hours": 3,
                "lab_hours": 2,
                "department": cse,
            },
        )
        cs102, _ = Course.objects.get_or_create(
            course_code="CS302",
            defaults={
                "title": "Operating Systems & Concurrency",
                "credits": 4,
                "lecture_hours": 3,
                "lab_hours": 2,
                "department": cse,
            },
        )

        # 5. Create Admin User
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@college.edu",
                "first_name": "System",
                "last_name": "Admin",
                "role": "ADMIN",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("admin123")
        admin_user.save()

        AdminProfile.objects.get_or_create(
            user=admin_user,
            defaults={"employee_code": "ADM-001", "designation": "Head Systems Administrator"},
        )

        # 6. Create Permanent Faculty (Senior Professor & PI)
        prof_user, _ = User.objects.get_or_create(
            username="dr_sharma",
            defaults={
                "email": "sharma@college.edu",
                "first_name": "Rajesh",
                "last_name": "Sharma",
                "role": "TEACHER",
            },
        )
        prof_user.set_password("pass123")
        prof_user.save()

        inst_sharma, _ = InstructorProfile.objects.get_or_create(
            user=prof_user,
            defaults={
                "employee_code": "FAC-CSE-001",
                "department": cse,
                "faculty_category": "PERMANENT",
                "designation": "Professor & Head of Department",
                "highest_qualification": "Ph.D. in Computer Science (IIT Bombay)",
                "hire_date": datetime.date(2010, 7, 15),
                "office_room": "CSE-Block-302",
            },
        )
        PermanentFaculty.objects.get_or_create(
            instructor=inst_sharma,
            defaults={
                "tenure_status": "TENURED",
                "provident_fund_no": "PF-CSE-9921",
                "pension_eligible": True,
            },
        )

        # 7. Create Assistant Professor (Tenure-Track, Mentored)
        asst_user, _ = User.objects.get_or_create(
            username="prof_neha",
            defaults={
                "email": "neha@college.edu",
                "first_name": "Neha",
                "last_name": "Verma",
                "role": "TEACHER",
            },
        )
        asst_user.set_password("pass123")
        asst_user.save()

        inst_neha, _ = InstructorProfile.objects.get_or_create(
            user=asst_user,
            defaults={
                "employee_code": "FAC-CSE-015",
                "department": cse,
                "faculty_category": "ASSISTANT_PROFESSOR",
                "designation": "Assistant Professor (Grade I)",
                "highest_qualification": "Ph.D. in Distributed Systems",
                "hire_date": datetime.date(2024, 8, 1),
                "office_room": "CSE-Block-214",
            },
        )
        AssistantProfessor.objects.get_or_create(
            instructor=inst_neha,
            defaults={
                "probation_end_date": datetime.date(2027, 8, 1),
                "tenure_review_date": datetime.date(2027, 5, 15),
                "mentor": inst_sharma,
                "publication_quota": 4,
            },
        )

        # 8. Create Visiting Professor
        visiting_user, _ = User.objects.get_or_create(
            username="prof_alok",
            defaults={
                "email": "alok@iitd.ac.in",
                "first_name": "Alok",
                "last_name": "Chatterjee",
                "role": "TEACHER",
            },
        )
        visiting_user.set_password("pass123")
        visiting_user.save()

        inst_alok, _ = InstructorProfile.objects.get_or_create(
            user=visiting_user,
            defaults={
                "employee_code": "FAC-VIS-004",
                "department": cse,
                "faculty_category": "VISITING",
                "designation": "Visiting Professor",
                "highest_qualification": "D.Sc. in Database Engineering",
                "hire_date": datetime.date(2026, 8, 1),
                "office_room": "Guest-Faculty-Wing-1",
            },
        )
        VisitingProfessor.objects.get_or_create(
            instructor=inst_alok,
            defaults={
                "home_institution": "IIT Delhi (Dept of CSE)",
                "contract_start_date": datetime.date(2026, 8, 1),
                "contract_end_date": datetime.date(2026, 12, 31),
                "honorarium_per_month": 75000.00,
                "max_weekly_lecture_hours": 6,
            },
        )

        # 9. Create Office Staff (Research Office & Accounts)
        staff_user, _ = User.objects.get_or_create(
            username="staff_sunita",
            defaults={
                "email": "sunita@college.edu",
                "first_name": "Sunita",
                "last_name": "Gupta",
                "role": "OFFICE_STAFF",
            },
        )
        staff_user.set_password("pass123")
        staff_user.save()

        staff_profile, _ = OfficeStaffProfile.objects.get_or_create(
            user=staff_user,
            defaults={
                "employee_code": "STAFF-RES-03",
                "section": "RESEARCH_OFFICE",
                "designation": "Research Project Accounts Superintendent",
            },
        )

        # 10. Create Students
        student_user, _ = User.objects.get_or_create(
            username="student_arjun",
            defaults={
                "email": "arjun@college.edu",
                "first_name": "Arjun",
                "last_name": "Mehta",
                "role": "STUDENT",
            },
        )
        student_user.set_password("pass123")
        student_user.save()

        student_arjun, _ = StudentProfile.objects.get_or_create(
            user=student_user,
            defaults={
                "roll_number": "2026CSE042",
                "registration_number": "REG-2026-00942",
                "program": btech_cse,
                "current_semester": 5,
                "admission_date": datetime.date(2024, 7, 20),
                "status": "ACTIVE",
            },
        )

        # 11. Course Offerings & Enrollments
        offering_dbms, _ = CourseOffering.objects.get_or_create(
            course=cs101,
            semester=current_sem,
            section_name="A",
            defaults={"instructor": inst_sharma, "max_capacity": 60},
        )
        offering_os, _ = CourseOffering.objects.get_or_create(
            course=cs102,
            semester=current_sem,
            section_name="A",
            defaults={"instructor": inst_neha, "max_capacity": 60},
        )

        Enrollment.objects.get_or_create(student=student_arjun, offering=offering_dbms)
        Enrollment.objects.get_or_create(student=student_arjun, offering=offering_os)

        # 12. Research Wing (Project, Co-PI, Juniors, Stipends)
        project_dst, _ = ResearchProject.objects.get_or_create(
            project_code="DST-SERB-2026-AI",
            defaults={
                "title": "Scalable Relational Query Optimization for Cloud-Native Distributed DBMS",
                "pi": inst_sharma,
                "funding_agency": "DST-SERB (Govt. of India)",
                "total_grant_amount": 4500000.00,  # 45 Lakhs
                "allocated_stipend_budget": 1200000.00,  # 12 Lakhs
                "start_date": datetime.date(2026, 1, 1),
                "end_date": datetime.date(2028, 12, 31),
                "status": "ACTIVE",
            },
        )

        ProjectCoInvestigator.objects.get_or_create(
            project=project_dst,
            instructor=inst_neha,
            defaults={"role_description": "Co-Principal Investigator (Concurrency Analysis)"},
        )

        # Research Juniors under Dr. Sharma
        junior_arjun, _ = ResearchJunior.objects.get_or_create(
            project=project_dst,
            full_name="Arjun Mehta",
            defaults={
                "student": student_arjun,
                "email": "arjun@college.edu",
                "phone": "+91 9876543210",
                "cadre": "STUDENT_INTERN",
                "monthly_stipend": 12000.00,
                "appointment_start_date": datetime.date(2026, 8, 1),
                "appointment_end_date": datetime.date(2026, 12, 31),
                "status": "ACTIVE",
            },
        )

        junior_priya, _ = ResearchJunior.objects.get_or_create(
            project=project_dst,
            full_name="Priya Nair",
            defaults={
                "email": "priya.jrf@college.edu",
                "phone": "+91 9811223344",
                "cadre": "JRF",
                "monthly_stipend": 37000.00,
                "appointment_start_date": datetime.date(2026, 2, 1),
                "appointment_end_date": datetime.date(2028, 1, 31),
                "status": "ACTIVE",
            },
        )

        # Monthly Stipends
        # Stipend 1: Approved by PI Dr. Sharma -> Waiting for Office Clearance
        StipendDisbursement.objects.get_or_create(
            junior=junior_priya,
            disbursement_month=9,
            disbursement_year=2026,
            defaults={
                "amount": 37000.00,
                "pi_approved": True,
                "pi_approval_date": datetime.date(2026, 10, 2),
                "office_processed": False,
                "payment_status": "APPROVED_BY_PI",
            },
        )

        # Stipend 2: Pending PI approval
        StipendDisbursement.objects.get_or_create(
            junior=junior_arjun,
            disbursement_month=9,
            disbursement_year=2026,
            defaults={
                "amount": 12000.00,
                "pi_approved": False,
                "office_processed": False,
                "payment_status": "PENDING_PI_APPROVAL",
            },
        )

        # Publications
        ResearchPublication.objects.get_or_create(
            instructor=inst_sharma,
            title="Adaptive Index Tuning in Partitioned Distributed Relational Databases",
            defaults={
                "project": project_dst,
                "venue_name": "IEEE Transactions on Knowledge and Data Engineering (TKDE)",
                "publication_type": "JOURNAL",
                "publication_date": datetime.date(2026, 6, 18),
                "doi_or_url": "10.1109/TKDE.2026.1049281",
                "impact_factor": 8.90,
            },
        )

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully!"))
        self.stdout.write(
            """
Demo Accounts Created:
---------------------------------------------------------------
Role               Username        Password
---------------------------------------------------------------
Admin              admin           admin123
Permanent Prof     dr_sharma       pass123
Assistant Prof     prof_neha       pass123
Visiting Prof      prof_alok       pass123
Office Staff       staff_sunita    pass123
Student            student_arjun   pass123
---------------------------------------------------------------
"""
        )
