from decimal import Decimal
from django.db import models
from django.utils import timezone


class Department(models.Model):
    code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100, unique=True)
    established_year = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.code})"


class Program(models.Model):
    DEGREE_LEVEL_CHOICES = (
        ('UNDERGRADUATE', 'Undergraduate (B.Tech / B.Sc)'),
        ('POSTGRADUATE', 'Postgraduate (M.Tech / M.Sc)'),
        ('DOCTORAL', 'Doctoral (Ph.D.)'),
    )
    department = models.ForeignKey(Department, on_delete=models.RESTRICT, related_name='programs')
    name = models.CharField(max_length=100)
    degree_level = models.CharField(max_length=20, choices=DEGREE_LEVEL_CHOICES)
    duration_years = models.IntegerField()
    total_semesters = models.IntegerField()

    class Meta:
        unique_together = ('department', 'name')

    def __str__(self):
        return f"{self.name} [{self.get_degree_level_display()}]"


class Course(models.Model):
    course_code = models.CharField(max_length=15, unique=True)
    title = models.CharField(max_length=120)
    credits = models.IntegerField()
    lecture_hours = models.IntegerField(default=3)
    lab_hours = models.IntegerField(default=0)
    department = models.ForeignKey(Department, on_delete=models.RESTRICT, related_name='courses')

    def __str__(self):
        return f"{self.course_code}: {self.title} ({self.credits} Credits)"


class AcademicSemester(models.Model):
    TERM_CHOICES = (
        ('AUTUMN', 'Autumn Semester'),
        ('WINTER', 'Winter Semester'),
        ('SUMMER', 'Summer Semester'),
        ('ODD', 'Odd Semester'),
        ('EVEN', 'Even Semester'),
        ('FALL', 'Autumn Semester'),
        ('SPRING', 'Winter Semester'),
    )
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    academic_year = models.CharField(max_length=9)  # e.g. '2026-2027'
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    class Meta:
        unique_together = ('term', 'academic_year')

    def __str__(self):
        current_str = " (Active)" if self.is_current else ""
        return f"{self.get_term_display()} {self.academic_year}{current_str}"


class CourseOffering(models.Model):
    course = models.ForeignKey(Course, on_delete=models.RESTRICT, related_name='offerings')
    semester = models.ForeignKey(AcademicSemester, on_delete=models.RESTRICT, related_name='offerings')
    instructor = models.ForeignKey('accounts.InstructorProfile', on_delete=models.RESTRICT, related_name='offerings')
    section_name = models.CharField(max_length=10)  # e.g., 'A', 'B'
    max_capacity = models.IntegerField(default=60)

    class Meta:
        unique_together = ('course', 'semester', 'section_name')

    def __str__(self):
        return f"{self.course.course_code} - Sec {self.section_name} ({self.semester})"


class Enrollment(models.Model):
    STATUS_CHOICES = (
        ('ENROLLED', 'Enrolled'),
        ('DROPPED', 'Dropped'),
        ('COMPLETED', 'Completed'),
    )
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='enrollments')
    offering = models.ForeignKey(CourseOffering, on_delete=models.RESTRICT, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ENROLLED')

    class Meta:
        unique_together = ('student', 'offering')

    def __str__(self):
        return f"{self.student.roll_number} enrolled in {self.offering}"


class StudentFeeAccount(models.Model):
    STATUS_CHOICES = (
        ('PAID', 'Fully Paid'),
        ('PARTIAL', 'Partial Due'),
        ('PENDING', 'Pending Payment'),
        ('OVERDUE', 'Overdue'),
    )
    student = models.ForeignKey('accounts.StudentProfile', on_delete=models.CASCADE, related_name='fee_accounts')
    semester = models.ForeignKey(AcademicSemester, on_delete=models.RESTRICT, related_name='student_fee_accounts')
    tuition_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('200000.00'))
    hostel_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('60000.00'))
    amenities_exam_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('40000.00'))
    total_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('300000.00'))
    scholarship_concession = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    due_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('student', 'semester')
        ordering = ['-semester__academic_year', 'student__roll_number']

    @property
    def net_applicable_fee(self):
        return max(Decimal('0.00'), self.total_fee - self.scholarship_concession)

    @property
    def total_paid(self):
        paid = self.payments.filter(status='CONFIRMED').aggregate(total=models.Sum('amount'))['total']
        return paid or Decimal('0.00')

    @property
    def remaining_fee(self):
        return max(Decimal('0.00'), self.net_applicable_fee - self.total_paid)

    def recalculate_status(self, save=True):
        today = timezone.localdate()
        rem = self.remaining_fee
        paid = self.total_paid

        if rem <= Decimal('0.00'):
            self.status = 'PAID'
        elif paid > Decimal('0.00'):
            if self.due_date and today > self.due_date:
                self.status = 'OVERDUE'
            else:
                self.status = 'PARTIAL'
        else:
            if self.due_date and today > self.due_date:
                self.status = 'OVERDUE'
            else:
                self.status = 'PENDING'

        if save:
            self.save(update_fields=['status', 'updated_at'])

    def __str__(self):
        return f'{self.student.roll_number} - {self.semester} (Rem: ₹{self.remaining_fee})'


class FeePayment(models.Model):
    METHOD_CHOICES = (
        ('SBI_COLLECT', 'SBI Collect'),
        ('NET_BANKING', 'Net Banking / NEFT'),
        ('UPI', 'UPI Payment'),
        ('DEMAND_DRAFT', 'Demand Draft (DD)'),
        ('CHALLAN', 'Bank Challan'),
        ('CASH', 'Cash Counter'),
    )
    STATUS_CHOICES = (
        ('CONFIRMED', 'Confirmed & Cleared'),
        ('PENDING_CLEARANCE', 'Pending Bank Clearance'),
        ('REFUNDED', 'Refunded / Reversed'),
    )
    fee_account = models.ForeignKey(StudentFeeAccount, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=30, choices=METHOD_CHOICES, default='SBI_COLLECT')
    transaction_reference = models.CharField(max_length=100, unique=True)
    receipt_number = models.CharField(max_length=60, unique=True)
    payment_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=25, choices=STATUS_CHOICES, default='CONFIRMED')
    recorded_by = models.ForeignKey(
        'accounts.OfficeStaffProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='recorded_payments'
    )
    remarks = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-payment_date']

    def __str__(self):
        return f'Payment ₹{self.amount} ({self.transaction_reference}) - {self.fee_account.student.roll_number}'
