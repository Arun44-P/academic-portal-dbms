import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone

from apps.accounts.models import StudentProfile, OfficeStaffProfile
from apps.academics.models import Enrollment, CourseOffering, Program, Course
from apps.research.models import ResearchJunior, StipendDisbursement


# ============================================================================
# STUDENT VIEWS
# ============================================================================

@login_required
def student_dashboard(request):
    if request.user.role != 'STUDENT':
        messages.error(request, "Access restricted to Students.")
        return redirect('accounts:role_dispatch')

    student = get_object_or_404(StudentProfile, user=request.user)
    enrollments = Enrollment.objects.filter(student=student).select_related(
        'offering__course', 'offering__semester', 'offering__instructor__user'
    )

    # Check if student is also attached as a Research Junior
    research_roles = ResearchJunior.objects.filter(student=student).select_related('project__pi__user')
    stipends = StipendDisbursement.objects.filter(junior__student=student).order_by('-disbursement_year', '-disbursement_month')

    total_credits = sum(e.offering.course.credits for e in enrollments if e.status == 'ENROLLED')

    return render(request, 'student/dashboard.html', {
        'student': student,
        'enrollments': enrollments,
        'research_roles': research_roles,
        'stipends': stipends,
        'total_credits': total_credits,
        'total_fee': 300000,
        'paid_fee': 200000,
        'due_fee': 100000,
    })


@login_required
def student_fee_status(request):
    if request.user.role != 'STUDENT':
        messages.error(request, "Access restricted to Students.")
        return redirect('accounts:role_dispatch')

    student = get_object_or_404(StudentProfile, user=request.user)
    return render(request, 'student/fee_status.html', {
        'student': student,
        'total_fee': 300000,
        'paid_fee': 200000,
        'due_fee': 100000,
    })


@login_required
def course_catalog(request):
    if request.user.role != 'STUDENT':
        messages.error(request, "Access restricted to Students.")
        return redirect('accounts:role_dispatch')

    student = get_object_or_404(StudentProfile, user=request.user)
    current_offerings = CourseOffering.objects.filter(
        semester__is_current=True
    ).select_related('course', 'instructor__user', 'semester')

    # Get IDs of currently enrolled offerings
    enrolled_offering_ids = set(
        Enrollment.objects.filter(student=student, status='ENROLLED')
        .values_list('offering_id', flat=True)
    )

    return render(request, 'student/courses.html', {
        'student': student,
        'offerings': current_offerings,
        'enrolled_ids': enrolled_offering_ids,
    })


@login_required
def enroll_course(request, offering_id):
    if request.user.role != 'STUDENT':
        messages.error(request, "Access denied.")
        return redirect('accounts:role_dispatch')

    student = get_object_or_404(StudentProfile, user=request.user)
    offering = get_object_or_404(CourseOffering, id=offering_id)

    # Check section capacity
    enrolled_count = Enrollment.objects.filter(offering=offering, status='ENROLLED').count()
    if enrolled_count >= offering.max_capacity:
        messages.error(
            request,
            f"Cannot enroll: Section {offering.section_name} is full ({offering.max_capacity}/{offering.max_capacity})."
        )
        return redirect('student:catalog')

    enrollment, created = Enrollment.objects.get_or_create(
        student=student,
        offering=offering,
        defaults={'status': 'ENROLLED'}
    )
    if not created and enrollment.status != 'ENROLLED':
        enrollment.status = 'ENROLLED'
        enrollment.save()

    messages.success(
        request,
        f"Enrolled successfully in {offering.course.course_code}: {offering.course.title} (Sec {offering.section_name})!"
    )
    return redirect('student:dashboard')


@login_required
def drop_course(request, enrollment_id):
    if request.user.role != 'STUDENT':
        messages.error(request, "Access denied.")
        return redirect('accounts:role_dispatch')

    student = get_object_or_404(StudentProfile, user=request.user)
    enrollment = get_object_or_404(Enrollment, id=enrollment_id, student=student)

    enrollment.status = 'DROPPED'
    enrollment.save()

    messages.info(request, f"Dropped course {enrollment.offering.course.course_code}.")
    return redirect('student:dashboard')


@login_required
def student_attendance_grades(request):
    if request.user.role != 'STUDENT':
        messages.error(request, "Access restricted to Students.")
        return redirect('accounts:role_dispatch')

    student = get_object_or_404(StudentProfile, user=request.user)
    enrollments = Enrollment.objects.filter(student=student, status='ENROLLED').select_related(
        'offering__course', 'offering__semester', 'offering__instructor__user'
    )

    return render(request, 'student/attendance_grades.html', {
        'student': student,
        'enrollments': enrollments,
    })


@login_required
def student_research_role(request):
    if request.user.role != 'STUDENT':
        messages.error(request, "Access restricted to Students.")
        return redirect('accounts:role_dispatch')

    student = get_object_or_404(StudentProfile, user=request.user)
    research_roles = ResearchJunior.objects.filter(student=student).select_related('project__pi__user')
    stipends = StipendDisbursement.objects.filter(junior__student=student).order_by('-disbursement_year', '-disbursement_month')

    return render(request, 'student/research_role.html', {
        'student': student,
        'research_roles': research_roles,
        'stipends': stipends,
    })


# ============================================================================
# OFFICE STAFF VIEWS
# ============================================================================

@login_required
def office_dashboard(request):
    if request.user.role != 'OFFICE_STAFF':
        messages.error(request, "Access restricted to Office Staff.")
        return redirect('accounts:role_dispatch')

    staff = get_object_or_404(OfficeStaffProfile, user=request.user)

    stipend_queue = StipendDisbursement.objects.filter(
        payment_status='APPROVED_BY_PI'
    ).select_related('junior__project__pi__user', 'junior__student')

    processed_stipends = StipendDisbursement.objects.filter(
        payment_status='PROCESSED'
    ).select_related('junior', 'processed_by__user').order_by('-disbursed_at')[:10]

    return render(request, 'office/dashboard.html', {
        'staff': staff,
        'stipend_queue': stipend_queue,
        'processed_stipends': processed_stipends,
        'total_programs': Program.objects.count(),
        'total_courses': Course.objects.count(),
        'active_offerings': CourseOffering.objects.count(),
    })


@login_required
def stipend_queue_view(request):
    if request.user.role != 'OFFICE_STAFF':
        messages.error(request, "Access restricted to Office Staff.")
        return redirect('accounts:role_dispatch')

    staff = get_object_or_404(OfficeStaffProfile, user=request.user)

    stipend_queue = StipendDisbursement.objects.filter(
        payment_status='APPROVED_BY_PI'
    ).select_related('junior__project__pi__user', 'junior__student')

    processed_stipends = StipendDisbursement.objects.filter(
        payment_status='PROCESSED'
    ).select_related('junior', 'processed_by__user').order_by('-disbursed_at')[:15]

    return render(request, 'office/stipend_queue.html', {
        'staff': staff,
        'stipend_queue': stipend_queue,
        'processed_stipends': processed_stipends,
    })


@login_required
def schedule_view(request):
    if request.user.role != 'OFFICE_STAFF':
        messages.error(request, "Access restricted to Office Staff.")
        return redirect('accounts:role_dispatch')

    staff = get_object_or_404(OfficeStaffProfile, user=request.user)
    offerings = CourseOffering.objects.all().select_related('course', 'instructor__user', 'semester')

    return render(request, 'office/schedule.html', {
        'staff': staff,
        'offerings': offerings,
    })


@login_required
def disburse_stipend(request, disbursement_id):
    if request.user.role != 'OFFICE_STAFF':
        messages.error(request, "Access denied.")
        return redirect('accounts:role_dispatch')

    staff = get_object_or_404(OfficeStaffProfile, user=request.user)
    stipend = get_object_or_404(StipendDisbursement, id=disbursement_id)

    if request.method == 'POST':
        tx_ref = request.POST.get('transaction_reference', '').strip()
        if not tx_ref:
            messages.error(request, "Transaction reference number is mandatory for financial disbursement.")
            next_url = request.POST.get('next') or 'office:dashboard'
            return redirect(next_url)

        stipend.office_processed = True
        stipend.processed_by = staff
        stipend.payment_status = 'PROCESSED'
        stipend.transaction_reference = tx_ref
        stipend.disbursed_at = timezone.now()
        stipend.save()

        messages.success(
            request,
            f"Stipend of ₹{stipend.amount} for {stipend.junior.full_name} marked DISBURSED (Ref: {tx_ref})!"
        )

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'office:dashboard'
    return redirect(next_url)
