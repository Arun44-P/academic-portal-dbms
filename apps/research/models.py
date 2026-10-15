from django.db import models
from django.core.exceptions import ValidationError


class ResearchProject(models.Model):
    STATUS_CHOICES = (
        ('PROPOSED', 'Proposed'),
        ('ACTIVE', 'Active'),
        ('COMPLETED', 'Completed'),
        ('TERMINATED', 'Terminated'),
    )
    project_code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=255)
    pi = models.ForeignKey(
        'accounts.InstructorProfile', on_delete=models.RESTRICT, related_name='pi_projects'
    )
    funding_agency = models.CharField(max_length=150)
    total_grant_amount = models.DecimalField(max_digits=12, decimal_places=2)
    allocated_stipend_budget = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.allocated_stipend_budget > self.total_grant_amount:
            raise ValidationError("Allocated stipend budget cannot exceed total grant amount.")
        if self.end_date <= self.start_date:
            raise ValidationError("Project end date must be after start date.")

    def __str__(self):
        return f"[{self.project_code}] {self.title} (PI: {self.pi.user.last_name})"


class ProjectCoInvestigator(models.Model):
    project = models.ForeignKey(ResearchProject, on_delete=models.CASCADE, related_name='co_investigators')
    instructor = models.ForeignKey(
        'accounts.InstructorProfile', on_delete=models.CASCADE, related_name='co_pi_projects'
    )
    role_description = models.CharField(max_length=100, default='Co-Principal Investigator')

    class Meta:
        unique_together = ('project', 'instructor')

    def __str__(self):
        return f"{self.instructor} - Co-PI on {self.project.project_code}"


class ResearchJunior(models.Model):
    CADRE_CHOICES = (
        ('JRF', 'Junior Research Fellow (JRF)'),
        ('SRF', 'Senior Research Fellow (SRF)'),
        ('PROJECT_ASSOCIATE', 'Project Associate'),
        ('PHD_FELLOW', 'Ph.D. Fellow'),
        ('STUDENT_INTERN', 'Student Intern'),
    )
    STATUS_CHOICES = (
        ('ACTIVE', 'Active'),
        ('RELIEVED', 'Relieved'),
        ('TERMINATED', 'Terminated'),
    )
    project = models.ForeignKey(ResearchProject, on_delete=models.RESTRICT, related_name='juniors')
    student = models.ForeignKey(
        'accounts.StudentProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='research_fellowships'
    )
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    cadre = models.CharField(max_length=30, choices=CADRE_CHOICES)
    monthly_stipend = models.DecimalField(max_digits=10, decimal_places=2)
    appointment_start_date = models.DateField()
    appointment_end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    def __str__(self):
        return f"{self.full_name} ({self.get_cadre_display()}) - {self.project.project_code}"


class StipendDisbursement(models.Model):
    STATUS_CHOICES = (
        ('PENDING_PI_APPROVAL', 'Pending PI Approval'),
        ('APPROVED_BY_PI', 'Approved by PI (Sent to Office)'),
        ('PROCESSED', 'Processed / Disbursed'),
        ('REJECTED', 'Rejected'),
    )
    junior = models.ForeignKey(ResearchJunior, on_delete=models.RESTRICT, related_name='stipends')
    disbursement_month = models.PositiveSmallIntegerField()  # 1 to 12
    disbursement_year = models.PositiveSmallIntegerField()
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    pi_approved = models.BooleanField(default=False)
    pi_approval_date = models.DateField(null=True, blank=True)
    office_processed = models.BooleanField(default=False)
    processed_by = models.ForeignKey(
        'accounts.OfficeStaffProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_stipends'
    )
    payment_status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='PENDING_PI_APPROVAL')
    transaction_reference = models.CharField(max_length=100, unique=True, null=True, blank=True)
    disbursed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('junior', 'disbursement_month', 'disbursement_year')

    def __str__(self):
        return f"Stipend: {self.junior.full_name} - {self.disbursement_month}/{self.disbursement_year} [₹{self.amount}] ({self.payment_status})"


class ResearchPublication(models.Model):
    PUB_TYPE_CHOICES = (
        ('JOURNAL', 'Journal Article'),
        ('CONFERENCE', 'Conference Paper'),
        ('PATENT', 'Patent'),
        ('BOOK_CHAPTER', 'Book Chapter'),
    )
    instructor = models.ForeignKey(
        'accounts.InstructorProfile', on_delete=models.CASCADE, related_name='publications'
    )
    project = models.ForeignKey(
        ResearchProject, on_delete=models.SET_NULL, null=True, blank=True, related_name='publications'
    )
    title = models.CharField(max_length=255)
    venue_name = models.CharField(max_length=200)
    publication_type = models.CharField(max_length=30, choices=PUB_TYPE_CHOICES)
    publication_date = models.DateField()
    doi_or_url = models.CharField(max_length=255, blank=True, null=True)
    impact_factor = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.title} ({self.venue_name}, {self.publication_date.year})"
