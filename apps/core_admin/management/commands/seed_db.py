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
    help = "Seeds database with IIIT Bhopal academic curriculum, requested professors, and student profiles."

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write("Starting IIIT Bhopal database seeding...")

        # 1. Departments
        cse, _ = Department.objects.get_or_create(
            code="CSE",
            defaults={"name": "Computer Science & Engineering", "established_year": 2017},
        )
        it, _ = Department.objects.get_or_create(
            code="IT",
            defaults={"name": "Information Technology", "established_year": 2017},
        )
        ece, _ = Department.objects.get_or_create(
            code="ECE",
            defaults={"name": "Electronics & Communication Engineering", "established_year": 2017},
        )

        # 2. Programs
        btech_cse, _ = Program.objects.get_or_create(
            department=cse,
            name="B.Tech Computer Science & Engineering",
            defaults={
                "degree_level": "UNDERGRADUATE",
                "duration_years": 4,
                "total_semesters": 8,
            },
        )
        btech_it, _ = Program.objects.get_or_create(
            department=it,
            name="B.Tech Information Technology",
            defaults={
                "degree_level": "UNDERGRADUATE",
                "duration_years": 4,
                "total_semesters": 8,
            },
        )

        # 3. Academic Semester (Autumn Semester 2026-27)
        # Deactivate any previous semesters
        AcademicSemester.objects.update(is_current=False)
        current_sem, _ = AcademicSemester.objects.get_or_create(
            term="AUTUMN",
            academic_year="2026-2027",
            defaults={
                "start_date": datetime.date(2026, 7, 20),
                "end_date": datetime.date(2026, 12, 10),
                "is_current": True,
            },
        )
        current_sem.is_current = True
        current_sem.save()

        # 4. IIIT Bhopal Courses
        c_dbms, _ = Course.objects.get_or_create(
            course_code="CS301",
            defaults={
                "title": "Database Management Systems",
                "credits": 4,
                "lecture_hours": 3,
                "lab_hours": 2,
                "department": cse,
            },
        )
        c_os, _ = Course.objects.get_or_create(
            course_code="CS302",
            defaults={
                "title": "Operating Systems",
                "credits": 4,
                "lecture_hours": 3,
                "lab_hours": 2,
                "department": cse,
            },
        )
        c_cn, _ = Course.objects.get_or_create(
            course_code="CS303",
            defaults={
                "title": "Computer Networks",
                "credits": 4,
                "lecture_hours": 3,
                "lab_hours": 2,
                "department": cse,
            },
        )
        c_daa, _ = Course.objects.get_or_create(
            course_code="CS304",
            defaults={
                "title": "Design and Analysis of Algorithms",
                "credits": 4,
                "lecture_hours": 3,
                "lab_hours": 2,
                "department": cse,
            },
        )
        c_se, _ = Course.objects.get_or_create(
            course_code="CS305",
            defaults={
                "title": "Software Engineering",
                "credits": 3,
                "lecture_hours": 3,
                "lab_hours": 0,
                "department": cse,
            },
        )
        c_wt, _ = Course.objects.get_or_create(
            course_code="IT301",
            defaults={
                "title": "Web Technologies & Cloud Computing",
                "credits": 3,
                "lecture_hours": 2,
                "lab_hours": 2,
                "department": it,
            },
        )
        c_mp, _ = Course.objects.get_or_create(
            course_code="EC301",
            defaults={
                "title": "Microprocessors & Embedded Systems",
                "credits": 3,
                "lecture_hours": 2,
                "lab_hours": 2,
                "department": ece,
            },
        )
        c_ai, _ = Course.objects.get_or_create(
            course_code="CS401",
            defaults={
                "title": "Machine Learning & Artificial Intelligence",
                "credits": 4,
                "lecture_hours": 3,
                "lab_hours": 2,
                "department": cse,
            },
        )

        # 5. Admin User (Password: pass123)
        admin_user, _ = User.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@iiitbhopal.ac.in",
                "first_name": "System",
                "last_name": "Admin",
                "role": "ADMIN",
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("pass123")
        admin_user.save()

        AdminProfile.objects.get_or_create(
            user=admin_user,
            defaults={"employee_code": "ADM-001", "designation": "Head Systems Administrator"},
        )

        # 6. Professors
        # Professor 1: Dr. Yatendra Sahu (Permanent Professor, HOD & Tenured PI)
        u_sahu, _ = User.objects.get_or_create(
            username="dr_sahu",
            defaults={
                "email": "ysahu@iiitbhopal.ac.in",
                "first_name": "Yatendra",
                "last_name": "Sahu",
                "role": "TEACHER",
            },
        )
        u_sahu.first_name = "Yatendra"
        u_sahu.last_name = "Sahu"
        u_sahu.set_password("pass123")
        u_sahu.save()

        inst_sahu, _ = InstructorProfile.objects.get_or_create(
            user=u_sahu,
            defaults={
                "employee_code": "FAC-CSE-001",
                "department": cse,
                "faculty_category": "PERMANENT",
                "designation": "Professor & Head of Department",
                "highest_qualification": "Ph.D. in Computer Science",
                "hire_date": datetime.date(2018, 7, 1),
                "office_room": "Faculty-Wing-101",
            },
        )
        PermanentFaculty.objects.get_or_create(
            instructor=inst_sahu,
            defaults={
                "tenure_status": "TENURED",
                "provident_fund_no": "PF-IIITB-001",
                "pension_eligible": True,
            },
        )

        # Professor 2: Dr. Rahul Chaurasia (Professor)
        u_chaurasia, _ = User.objects.get_or_create(
            username="dr_chaurasia",
            defaults={
                "email": "rchaurasia@iiitbhopal.ac.in",
                "first_name": "Rahul",
                "last_name": "Chaurasia",
                "role": "TEACHER",
            },
        )
        u_chaurasia.first_name = "Rahul"
        u_chaurasia.last_name = "Chaurasia"
        u_chaurasia.set_password("pass123")
        u_chaurasia.save()

        inst_chaurasia, _ = InstructorProfile.objects.get_or_create(
            user=u_chaurasia,
            defaults={
                "employee_code": "FAC-CSE-002",
                "department": cse,
                "faculty_category": "PERMANENT",
                "designation": "Professor",
                "highest_qualification": "Ph.D. in Operating Systems & Architecture",
                "hire_date": datetime.date(2019, 8, 1),
                "office_room": "Faculty-Wing-102",
            },
        )
        PermanentFaculty.objects.get_or_create(
            instructor=inst_chaurasia,
            defaults={
                "tenure_status": "TENURED",
                "provident_fund_no": "PF-IIITB-002",
                "pension_eligible": True,
            },
        )

        # Professor 3: Dr. Neha Kakkar (Assistant Professor)
        u_neha, _ = User.objects.get_or_create(
            username="prof_neha",
            defaults={
                "email": "nkakkar@iiitbhopal.ac.in",
                "first_name": "Neha",
                "last_name": "Kakkar",
                "role": "TEACHER",
            },
        )
        u_neha.first_name = "Neha"
        u_neha.last_name = "Kakkar"
        u_neha.set_password("pass123")
        u_neha.save()

        inst_neha, _ = InstructorProfile.objects.get_or_create(
            user=u_neha,
            defaults={
                "employee_code": "FAC-CSE-015",
                "department": cse,
                "faculty_category": "ASSISTANT_PROFESSOR",
                "designation": "Assistant Professor",
                "highest_qualification": "Ph.D. in Computer Networks & Distributed Systems",
                "hire_date": datetime.date(2022, 1, 15),
                "office_room": "Faculty-Wing-204",
            },
        )
        AssistantProfessor.objects.get_or_create(
            instructor=inst_neha,
            defaults={
                "probation_end_date": datetime.date(2027, 1, 15),
                "tenure_review_date": datetime.date(2026, 12, 1),
                "mentor": inst_sahu,
                "publication_quota": 4,
            },
        )

        # 7. Office Staff
        u_staff, _ = User.objects.get_or_create(
            username="staff_sunita",
            defaults={
                "email": "sunita@iiitbhopal.ac.in",
                "first_name": "Sunita",
                "last_name": "Gupta",
                "role": "OFFICE_STAFF",
            },
        )
        u_staff.set_password("pass123")
        u_staff.save()

        OfficeStaffProfile.objects.get_or_create(
            user=u_staff,
            defaults={
                "employee_code": "STAFF-ADM-01",
                "section": "RESEARCH_OFFICE",
                "designation": "Accounts & Academic Administration Superintendent",
            },
        )

        # 8. Students
        # Student 1: Atharv Pathak
        u_atharv, _ = User.objects.get_or_create(
            username="atharv_pathak",
            defaults={
                "email": "atharv@iiitbhopal.ac.in",
                "first_name": "Atharv",
                "last_name": "Pathak",
                "role": "STUDENT",
            },
        )
        u_atharv.first_name = "Atharv"
        u_atharv.last_name = "Pathak"
        u_atharv.set_password("pass123")
        u_atharv.save()

        s_atharv, _ = StudentProfile.objects.get_or_create(
            user=u_atharv,
            defaults={
                "roll_number": "2024BCS001",
                "registration_number": "REG-IIITB-2024-001",
                "program": btech_cse,
                "current_semester": 5,
                "admission_date": datetime.date(2024, 7, 15),
                "status": "ACTIVE",
            },
        )

        # Student 2: Arun Patidar
        u_arun, _ = User.objects.get_or_create(
            username="arun_patidar",
            defaults={
                "email": "arun@iiitbhopal.ac.in",
                "first_name": "Arun",
                "last_name": "Patidar",
                "role": "STUDENT",
            },
        )
        u_arun.first_name = "Arun"
        u_arun.last_name = "Patidar"
        u_arun.set_password("pass123")
        u_arun.save()

        s_arun, _ = StudentProfile.objects.get_or_create(
            user=u_arun,
            defaults={
                "roll_number": "2024BCS002",
                "registration_number": "REG-IIITB-2024-002",
                "program": btech_cse,
                "current_semester": 5,
                "admission_date": datetime.date(2024, 7, 15),
                "status": "ACTIVE",
            },
        )

        # Student 3: Prashast Mathur
        u_prashast, _ = User.objects.get_or_create(
            username="prashast_mathur",
            defaults={
                "email": "prashast@iiitbhopal.ac.in",
                "first_name": "Prashast",
                "last_name": "Mathur",
                "role": "STUDENT",
            },
        )
        u_prashast.first_name = "Prashast"
        u_prashast.last_name = "Mathur"
        u_prashast.set_password("pass123")
        u_prashast.save()

        s_prashast, _ = StudentProfile.objects.get_or_create(
            user=u_prashast,
            defaults={
                "roll_number": "2024BCS003",
                "registration_number": "REG-IIITB-2024-003",
                "program": btech_cse,
                "current_semester": 5,
                "admission_date": datetime.date(2024, 7, 15),
                "status": "ACTIVE",
            },
        )

        # 9. Course Offerings
        off_dbms, _ = CourseOffering.objects.get_or_create(
            course=c_dbms,
            semester=current_sem,
            section_name="A",
            defaults={"instructor": inst_sahu, "max_capacity": 65},
        )
        off_os, _ = CourseOffering.objects.get_or_create(
            course=c_os,
            semester=current_sem,
            section_name="A",
            defaults={"instructor": inst_chaurasia, "max_capacity": 65},
        )
        off_cn, _ = CourseOffering.objects.get_or_create(
            course=c_cn,
            semester=current_sem,
            section_name="A",
            defaults={"instructor": inst_neha, "max_capacity": 65},
        )
        off_daa, _ = CourseOffering.objects.get_or_create(
            course=c_daa,
            semester=current_sem,
            section_name="A",
            defaults={"instructor": inst_sahu, "max_capacity": 65},
        )
        off_se, _ = CourseOffering.objects.get_or_create(
            course=c_se,
            semester=current_sem,
            section_name="A",
            defaults={"instructor": inst_chaurasia, "max_capacity": 65},
        )
        off_wt, _ = CourseOffering.objects.get_or_create(
            course=c_wt,
            semester=current_sem,
            section_name="A",
            defaults={"instructor": inst_neha, "max_capacity": 65},
        )

        # 10. Enrollments
        # Atharv enrolled in CS301, CS302, CS303, CS304
        for off in [off_dbms, off_os, off_cn, off_daa]:
            Enrollment.objects.get_or_create(student=s_atharv, offering=off, defaults={"status": "ENROLLED"})

        # Arun enrolled in CS301, CS302, CS303, CS305
        for off in [off_dbms, off_os, off_cn, off_se]:
            Enrollment.objects.get_or_create(student=s_arun, offering=off, defaults={"status": "ENROLLED"})

        # Prashast enrolled in CS301, CS303, CS304, IT301
        for off in [off_dbms, off_cn, off_daa, off_wt]:
            Enrollment.objects.get_or_create(student=s_prashast, offering=off, defaults={"status": "ENROLLED"})

        # 11. Research Wing (DST Grant under Dr. Yatendra Sahu)
        project_dst, _ = ResearchProject.objects.get_or_create(
            project_code="DST-SERB-2026-IIITB",
            defaults={
                "title": "Scalable Relational Query Optimization for Cloud-Native Distributed DBMS",
                "pi": inst_sahu,
                "funding_agency": "DST-SERB (Govt. of India)",
                "total_grant_amount": 4500000.00,  # 45 Lakhs
                "allocated_stipend_budget": 1200000.00,  # 12 Lakhs
                "start_date": datetime.date(2026, 1, 1),
                "end_date": datetime.date(2028, 12, 31),
                "status": "ACTIVE",
            },
        )
        project_dst.pi = inst_sahu
        project_dst.save()

        ProjectCoInvestigator.objects.get_or_create(
            project=project_dst,
            instructor=inst_neha,
            defaults={"role_description": "Co-Principal Investigator (Concurrency Analysis)"},
        )

        # Research Juniors (Atharv Pathak & Arun Patidar attached to DST Grant)
        junior_atharv, _ = ResearchJunior.objects.get_or_create(
            project=project_dst,
            full_name="Atharv Pathak",
            defaults={
                "student": s_atharv,
                "email": "atharv@iiitbhopal.ac.in",
                "phone": "+91 9876543210",
                "cadre": "STUDENT_INTERN",
                "monthly_stipend": 12000.00,
                "appointment_start_date": datetime.date(2026, 8, 1),
                "appointment_end_date": datetime.date(2026, 12, 31),
                "status": "ACTIVE",
            },
        )
        junior_atharv.student = s_atharv
        junior_atharv.save()

        junior_arun, _ = ResearchJunior.objects.get_or_create(
            project=project_dst,
            full_name="Arun Patidar",
            defaults={
                "student": s_arun,
                "email": "arun@iiitbhopal.ac.in",
                "phone": "+91 9811223344",
                "cadre": "STUDENT_INTERN",
                "monthly_stipend": 12000.00,
                "appointment_start_date": datetime.date(2026, 8, 1),
                "appointment_end_date": datetime.date(2026, 12, 31),
                "status": "ACTIVE",
            },
        )
        junior_arun.student = s_arun
        junior_arun.save()

        # Monthly Stipends
        # Stipend 1 for Atharv: PENDING_PI_APPROVAL (Dr. Sahu can approve it in 1-click)
        StipendDisbursement.objects.filter(junior=junior_atharv, disbursement_month=9, disbursement_year=2026).delete()
        StipendDisbursement.objects.create(
            junior=junior_atharv,
            disbursement_month=9,
            disbursement_year=2026,
            amount=12000.00,
            pi_approved=False,
            office_processed=False,
            payment_status="PENDING_PI_APPROVAL",
        )

        # Stipend 2 for Arun: APPROVED_BY_PI (Waiting for Office Staff Sunita to disburse funds)
        StipendDisbursement.objects.filter(junior=junior_arun, disbursement_month=9, disbursement_year=2026).delete()
        StipendDisbursement.objects.create(
            junior=junior_arun,
            disbursement_month=9,
            disbursement_year=2026,
            amount=12000.00,
            pi_approved=True,
            pi_approval_date=datetime.date(2026, 10, 5),
            office_processed=False,
            payment_status="APPROVED_BY_PI",
        )

        # 12. Publications
        ResearchPublication.objects.get_or_create(
            instructor=inst_sahu,
            title="Adaptive Query Optimization & Normalization Models for IIIT Distributed Cloud Systems",
            defaults={
                "project": project_dst,
                "venue_name": "IEEE Transactions on Knowledge and Data Engineering (TKDE)",
                "publication_type": "JOURNAL",
                "publication_date": datetime.date(2026, 6, 18),
                "doi_or_url": "10.1109/TKDE.2026.1049281",
                "impact_factor": 8.90,
            },
        )

        self.stdout.write(self.style.SUCCESS("Database seeding completed successfully for IIIT Bhopal!"))
        self.stdout.write(
            """
Demo Accounts (Password for ALL is 'pass123'):
---------------------------------------------------------------------------------
Role               Full Name           Username          Password
---------------------------------------------------------------------------------
Admin              System Admin        admin             pass123
Permanent Prof     Dr. Yatendra Sahu   dr_sahu           pass123
Permanent Prof     Dr. Rahul Chaurasia dr_chaurasia      pass123
Assistant Prof     Dr. Neha Kakkar     prof_neha         pass123
Office Staff       Sunita Gupta        staff_sunita      pass123
Student            Atharv Pathak       atharv_pathak     pass123
Student            Arun Patidar        arun_patidar      pass123
Student            Prashast Mathur     prashast_mathur   pass123
---------------------------------------------------------------------------------
Fee Details: Total: Rs. 3,00,000 | Paid: Rs. 2,00,000 | Due: Rs. 1,00,000
Course Structure: IIIT Bhopal (CS301, CS302, CS303, CS304, CS305, IT301, EC301, CS401)
"""
        )
