from django.db import models
from django.contrib.auth.models import AbstractUser


class UserAccount(AbstractUser):
    ROLE_CHOICES = (
        ('ADMIN', 'Administrator'),
        ('FACULTY', 'Faculty'),
        ('OFFICE_STAFF', 'Office Staff'),
        ('STUDENT', 'Student'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def is_student(self):
        return self.role == 'STUDENT'

    @property
    def is_faculty(self):
        return self.role in ('FACULTY', 'TEACHER')

    @property
    def is_office_staff(self):
        return self.role in ('OFFICE_STAFF', 'OFFICE')

    @property
    def is_administrator(self):
        return self.role == 'ADMIN'

    def sync_group_membership(self):
        """Synchronizes user into the matching Django Group for their primary business role."""
        from django.contrib.auth.models import Group
        role_group_name = 'FACULTY' if self.role in ('FACULTY', 'TEACHER') else self.role
        try:
            group, _ = Group.objects.get_or_create(name=role_group_name)
            self.groups.add(group)
            other_groups = Group.objects.filter(name__in=['ADMIN', 'FACULTY', 'OFFICE_STAFF', 'STUDENT']).exclude(name=role_group_name)
            self.groups.remove(*other_groups)
        except Exception:
            pass

    def save(self, *args, **kwargs):
        # Normalize legacy 'TEACHER' role to 'FACULTY'
        if self.role == 'TEACHER':
            self.role = 'FACULTY'
        super().save(*args, **kwargs)
        if self.pk:
            self.sync_group_membership()

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class AdminProfile(models.Model):
    user = models.OneToOneField(
        UserAccount, on_delete=models.CASCADE, primary_key=True, related_name='admin_profile'
    )
    employee_code = models.CharField(max_length=30, unique=True)
    designation = models.CharField(max_length=50, default='System Administrator')
    is_superadmin = models.BooleanField(default=True)

    def __str__(self):
        return f"Admin: {self.user.get_full_name() or self.user.username} [{self.employee_code}]"


class OfficeStaffProfile(models.Model):
    SECTION_CHOICES = (
        ('ACCOUNTS', 'Accounts & Finance'),
        ('ADMISSIONS', 'Admissions'),
        ('EXAMINATIONS', 'Examinations'),
        ('RESEARCH_OFFICE', 'Research Office'),
        ('GENERAL_ADMIN', 'General Administration'),
    )
    user = models.OneToOneField(
        UserAccount, on_delete=models.CASCADE, primary_key=True, related_name='staff_profile'
    )
    employee_code = models.CharField(max_length=30, unique=True)
    section = models.CharField(max_length=30, choices=SECTION_CHOICES)
    designation = models.CharField(max_length=50)

    def __str__(self):
        return f"Staff: {self.user.get_full_name() or self.user.username} ({self.get_section_display()})"


class InstructorProfile(models.Model):
    CATEGORY_CHOICES = (
        ('PERMANENT', 'Permanent Faculty'),
        ('ASSISTANT_PROFESSOR', 'Assistant Professor'),
        ('VISITING', 'Visiting Professor'),
    )
    user = models.OneToOneField(
        UserAccount, on_delete=models.CASCADE, primary_key=True, related_name='instructor_profile'
    )
    employee_code = models.CharField(max_length=30, unique=True)
    department = models.ForeignKey(
        'academics.Department', on_delete=models.RESTRICT, related_name='instructors'
    )
    faculty_category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    designation = models.CharField(max_length=60)
    highest_qualification = models.CharField(max_length=100)
    hire_date = models.DateField()
    office_room = models.CharField(max_length=30, blank=True, null=True)

    def __str__(self):
        return f"Prof. {self.user.get_full_name() or self.user.username} [{self.department.code}]"


class PermanentFaculty(models.Model):
    TENURE_CHOICES = (
        ('TENURED', 'Tenured'),
        ('EMERITUS', 'Emeritus'),
    )
    instructor = models.OneToOneField(
        InstructorProfile, on_delete=models.CASCADE, primary_key=True, related_name='permanent_details'
    )
    tenure_status = models.CharField(max_length=20, choices=TENURE_CHOICES, default='TENURED')
    provident_fund_no = models.CharField(max_length=50, unique=True)
    pension_eligible = models.BooleanField(default=True)

    def __str__(self):
        return f"Permanent: {self.instructor} (PF: {self.provident_fund_no})"


class AssistantProfessor(models.Model):
    instructor = models.OneToOneField(
        InstructorProfile, on_delete=models.CASCADE, primary_key=True, related_name='assistant_details'
    )
    probation_end_date = models.DateField()
    tenure_review_date = models.DateField()
    mentor = models.ForeignKey(
        InstructorProfile, on_delete=models.SET_NULL, null=True, blank=True, related_name='mentees'
    )
    publication_quota = models.IntegerField(default=3)

    def __str__(self):
        return f"Assistant Prof: {self.instructor}"


class VisitingProfessor(models.Model):
    instructor = models.OneToOneField(
        InstructorProfile, on_delete=models.CASCADE, primary_key=True, related_name='visiting_details'
    )
    home_institution = models.CharField(max_length=150)
    contract_start_date = models.DateField()
    contract_end_date = models.DateField()
    honorarium_per_month = models.DecimalField(max_digits=10, decimal_places=2)
    max_weekly_lecture_hours = models.IntegerField(default=8)

    def __str__(self):
        return f"Visiting Prof: {self.instructor} ({self.home_institution})"


class StudentProfile(models.Model):
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('ALUMNI', 'Alumni'),
        ('WITHDRAWN', 'Withdrawn'),
    )
    user = models.OneToOneField(
        UserAccount, on_delete=models.CASCADE, primary_key=True, related_name='student_profile'
    )
    roll_number = models.CharField(max_length=30, unique=True)
    registration_number = models.CharField(max_length=30, unique=True)
    program = models.ForeignKey(
        'academics.Program', on_delete=models.RESTRICT, related_name='students'
    )
    current_semester = models.IntegerField(default=1)
    admission_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    def __str__(self):
        return f"{self.roll_number} - {self.user.get_full_name() or self.user.username}"
