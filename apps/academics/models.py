from django.db import models


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
