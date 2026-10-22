import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Q, Sum
from django.core.paginator import Paginator
from django.http import JsonResponse

from apps.accounts.models import StudentProfile, OfficeStaffProfile
from apps.academics.models import (
    Enrollment, CourseOffering, Program, Course, Department, AcademicSemester,
    StudentFeeAccount, FeePayment
)
from apps.research.models import ResearchJunior, StipendDisbursement
from apps.core_admin.models import AdminAuditLog


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

    total_credits = sum(e.offering.course.credits for e in enrollments if e.status == 'ENROLLED')

    # Real DB fee account
    fee_account = StudentFeeAccount.objects.filter(student=student).order_by('-semester__academic_year').first()
    if fee_account:
        fee_account.recalculate_status()
        total_fee = fee_account.net_applicable_fee
        paid_fee = fee_account.total_paid
        due_fee = fee_account.remaining_fee
    else:
        total_fee = Decimal('300000.00')
        paid_fee = Decimal('0.00')
        due_fee = Decimal('300000.00')

    return render(request, 'student/dashboard.html', {
        'student': student,
        'enrollments': enrollments,
        'total_credits': total_credits,
        'fee_account': fee_account,
        'total_fee': total_fee,
        'paid_fee': paid_fee,
        'due_fee': due_fee,
    })


@login_required
def student_fee_status(request):
    if request.user.role != 'STUDENT':
        messages.error(request, "Access restricted to Students.")
        return redirect('accounts:role_dispatch')

    student = get_object_or_404(StudentProfile, user=request.user)
    fee_account = StudentFeeAccount.objects.filter(student=student).order_by('-semester__academic_year').first()
    payments = []
    if fee_account:
        fee_account.recalculate_status()
        total_fee = fee_account.net_applicable_fee
        paid_fee = fee_account.total_paid
        due_fee = fee_account.remaining_fee
        payments = fee_account.payments.all()
    else:
        total_fee = Decimal('300000.00')
        paid_fee = Decimal('0.00')
        due_fee = Decimal('300000.00')

    return render(request, 'student/fee_status.html', {
        'student': student,
        'fee_account': fee_account,
        'payments': payments,
        'total_fee': total_fee,
        'paid_fee': paid_fee,
        'due_fee': due_fee,
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
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('student:dashboard')


# ============================================================================
# OFFICE STAFF VIEWS - STUDENT FEE MANAGEMENT
# ============================================================================

@login_required
def office_dashboard(request):
    if request.user.role not in ['OFFICE_STAFF', 'ADMIN']:
        messages.error(request, "Access restricted to Office Staff.")
        return redirect('accounts:role_dispatch')

    staff = OfficeStaffProfile.objects.filter(user=request.user).first()

    # Query all StudentFeeAccount records with related models
    accounts_qs = StudentFeeAccount.objects.select_related(
        'student__user', 'student__program__department', 'semester'
    ).prefetch_related('payments')

    # Recalculate status dynamically
    for acc in accounts_qs:
        acc.recalculate_status()

    all_accounts = list(accounts_qs)
    total_applicable = sum(acc.net_applicable_fee for acc in all_accounts)
    total_collected = sum(acc.total_paid for acc in all_accounts)
    total_outstanding = sum(acc.remaining_fee for acc in all_accounts)
    pending_students_count = sum(1 for acc in all_accounts if acc.remaining_fee > Decimal('0.00'))
    overdue_students_count = sum(1 for acc in all_accounts if acc.status == 'OVERDUE')
    total_students_count = len(all_accounts)
    collection_rate = (total_collected / total_applicable * 100) if total_applicable > 0 else Decimal('0.0')

    # Filtering & Searching
    search_q = request.GET.get('q', '').strip()
    selected_dept = request.GET.get('department', '').strip()
    selected_sem = request.GET.get('semester', '').strip()
    selected_status = request.GET.get('status', '').strip()
    selected_sort = request.GET.get('sort', 'remaining_desc').strip()

    filtered_accounts = accounts_qs

    if search_q:
        filtered_accounts = filtered_accounts.filter(
            Q(student__user__first_name__icontains=search_q) |
            Q(student__user__last_name__icontains=search_q) |
            Q(student__user__username__icontains=search_q) |
            Q(student__roll_number__icontains=search_q) |
            Q(student__program__name__icontains=search_q) |
            Q(student__program__department__code__icontains=search_q) |
            Q(student__program__department__name__icontains=search_q)
        )

    if selected_dept:
        filtered_accounts = filtered_accounts.filter(student__program__department__code=selected_dept)

    if selected_sem:
        filtered_accounts = filtered_accounts.filter(student__current_semester=selected_sem)

    if selected_status:
        filtered_accounts = filtered_accounts.filter(status=selected_status)

    account_list = list(filtered_accounts)
    if selected_sort == 'remaining_desc':
        account_list.sort(key=lambda a: a.remaining_fee, reverse=True)
    elif selected_sort == 'remaining_asc':
        account_list.sort(key=lambda a: a.remaining_fee)
    elif selected_sort == 'due_date_asc':
        account_list.sort(key=lambda a: a.due_date or datetime.date.max)
    elif selected_sort == 'roll_asc':
        account_list.sort(key=lambda a: a.student.roll_number)
    else:
        account_list.sort(key=lambda a: a.remaining_fee, reverse=True)

    # Pagination
    paginator = Paginator(account_list, 10)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    departments = Department.objects.all().order_by('code')
    available_semesters = sorted(list(set(StudentProfile.objects.values_list('current_semester', flat=True))))

    return render(request, 'office/dashboard.html', {
        'staff': staff,
        'summary': {
            'total_outstanding': total_outstanding,
            'students_pending': pending_students_count,
            'total_collected': total_collected,
            'overdue_count': overdue_students_count,
            'total_students': total_students_count,
            'collection_rate': round(collection_rate, 1),
        },
        'page_obj': page_obj,
        'departments': departments,
        'semesters': available_semesters,
        'search_q': search_q,
        'selected_dept': selected_dept,
        'selected_sem': selected_sem,
        'selected_status': selected_status,
        'selected_sort': selected_sort,
        'status_choices': StudentFeeAccount.STATUS_CHOICES,
        'payment_methods': FeePayment.METHOD_CHOICES,
    })


@login_required
def student_fee_detail_view(request, account_id):
    if request.user.role not in ['OFFICE_STAFF', 'ADMIN']:
        messages.error(request, "Access restricted to Office Staff.")
        return redirect('accounts:role_dispatch')

    staff = OfficeStaffProfile.objects.filter(user=request.user).first()
    account = get_object_or_404(
        StudentFeeAccount.objects.select_related(
            'student__user', 'student__program__department', 'semester'
        ),
        id=account_id
    )
    account.recalculate_status()
    payments = account.payments.select_related('recorded_by__user').all()

    # If requested via AJAX or JSON format
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
        payments_data = [
            {
                'id': p.id,
                'amount': f"{p.amount:,.2f}",
                'method': p.get_payment_method_display(),
                'reference': p.transaction_reference,
                'receipt': p.receipt_number,
                'date': p.payment_date.strftime('%d %b %Y, %I:%M %p'),
                'status': p.get_status_display(),
                'recorded_by': (p.recorded_by.user.get_full_name() or p.recorded_by.user.username) if p.recorded_by else 'System / Bank Gateway',
                'remarks': p.remarks or 'N/A',
            }
            for p in payments
        ]
        return JsonResponse({
            'success': True,
            'account_id': account.id,
            'student_name': account.student.user.get_full_name() or account.student.user.username,
            'roll_number': account.student.roll_number,
            'registration_number': account.student.registration_number,
            'program': account.student.program.name,
            'department': account.student.program.department.name,
            'department_code': account.student.program.department.code,
            'semester': f"Semester {account.student.current_semester} ({account.semester.get_term_display()} {account.semester.academic_year})",
            'total_fee': f"{account.total_fee:,.2f}",
            'tuition_fee': f"{account.tuition_fee:,.2f}",
            'hostel_fee': f"{account.hostel_fee:,.2f}",
            'amenities_exam_fee': f"{account.amenities_exam_fee:,.2f}",
            'scholarship_concession': f"{account.scholarship_concession:,.2f}",
            'net_applicable_fee': f"{account.net_applicable_fee:,.2f}",
            'total_paid': f"{account.total_paid:,.2f}",
            'remaining_fee': f"{account.remaining_fee:,.2f}",
            'due_date': account.due_date.strftime('%d %b %Y') if account.due_date else 'N/A',
            'status': account.status,
            'status_display': account.get_status_display(),
            'payments': payments_data,
        })

    return render(request, 'office/fee_detail.html', {
        'staff': staff,
        'account': account,
        'payments': payments,
        'payment_methods': FeePayment.METHOD_CHOICES,
    })


@login_required
def record_fee_payment(request, account_id):
    if request.user.role not in ['OFFICE_STAFF', 'ADMIN']:
        messages.error(request, "Access restricted to authorized Office Staff.")
        return redirect('accounts:role_dispatch')

    staff = OfficeStaffProfile.objects.filter(user=request.user).first()
    account = get_object_or_404(StudentFeeAccount, id=account_id)

    if request.method == 'POST':
        amount_str = request.POST.get('amount', '').strip()
        payment_method = request.POST.get('payment_method', 'SBI_COLLECT').strip()
        transaction_ref = request.POST.get('transaction_reference', '').strip()
        remarks = request.POST.get('remarks', '').strip()

        # Strict validation
        try:
            amount = Decimal(amount_str)
            if amount <= Decimal('0.00'):
                raise ValueError("Amount must be greater than zero.")
        except Exception:
            messages.error(request, "Invalid payment amount. Please enter a valid positive number.")
            return redirect('office:dashboard')

        if amount > account.remaining_fee:
            messages.error(
                request,
                f"Entered amount (₹{amount:,.2f}) exceeds student remaining fee (₹{account.remaining_fee:,.2f})."
            )
            return redirect('office:dashboard')

        if not transaction_ref:
            transaction_ref = f"MAN-{timezone.now().strftime('%Y%m%d%H%M%S')}-{account.student.roll_number[-4:]}"

        if FeePayment.objects.filter(transaction_reference=transaction_ref).exists():
            messages.error(request, f"A transaction with reference '{transaction_ref}' already exists in the system.")
            return redirect('office:dashboard')

        receipt_num = f"RCP-{timezone.now().strftime('%Y')}-{timezone.now().strftime('%m%d%H%M%S')}"

        with transaction.atomic():
            FeePayment.objects.create(
                fee_account=account,
                amount=amount,
                payment_method=payment_method,
                transaction_reference=transaction_ref,
                receipt_number=receipt_num,
                payment_date=timezone.now(),
                status='CONFIRMED',
                recorded_by=staff,
                remarks=remarks or f"Counter payment recorded by {request.user.username}"
            )
            account.recalculate_status(save=True)

            if hasattr(request.user, 'admin_profile'):
                AdminAuditLog.objects.create(
                    admin=request.user.admin_profile,
                    action_type='RAW_SQL_EXECUTE',
                    target_entity=f"StudentFeeAccount:{account.id}",
                    query_or_command=f"Recorded Payment ₹{amount} (Ref: {transaction_ref})",
                    justification_reason=remarks or "Manual fee collection at accounts desk",
                    ip_address=request.META.get('REMOTE_ADDR', '127.0.0.1'),
                    status='EXECUTED'
                )

        messages.success(
            request,
            f"Payment of ₹{amount:,.2f} recorded successfully for {account.student.user.get_full_name() or account.student.roll_number}! Receipt: {receipt_num}."
        )
        return redirect('office:dashboard')

    return redirect('office:dashboard')


@login_required
def office_payment_history(request):
    if request.user.role not in ['OFFICE_STAFF', 'ADMIN']:
        messages.error(request, "Access restricted to Office Staff.")
        return redirect('accounts:role_dispatch')

    staff = OfficeStaffProfile.objects.filter(user=request.user).first()
    payments_qs = FeePayment.objects.select_related(
        'fee_account__student__user',
        'fee_account__student__program__department',
        'fee_account__semester',
        'recorded_by__user'
    ).order_by('-payment_date')

    search_q = request.GET.get('q', '').strip()
    if search_q:
        payments_qs = payments_qs.filter(
            Q(transaction_reference__icontains=search_q) |
            Q(receipt_number__icontains=search_q) |
            Q(fee_account__student__roll_number__icontains=search_q) |
            Q(fee_account__student__user__first_name__icontains=search_q) |
            Q(fee_account__student__user__last_name__icontains=search_q)
        )

    paginator = Paginator(payments_qs, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)

    total_amount = payments_qs.filter(status='CONFIRMED').aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

    return render(request, 'office/payment_history.html', {
        'staff': staff,
        'page_obj': page_obj,
        'search_q': search_q,
        'total_amount': total_amount,
    })


@login_required
def schedule_view(request):
    if request.user.role not in ['OFFICE_STAFF', 'ADMIN']:
        messages.error(request, "Access restricted to Office Staff.")
        return redirect('accounts:role_dispatch')

    staff = OfficeStaffProfile.objects.filter(user=request.user).first()
    offerings = CourseOffering.objects.all().select_related('course', 'instructor__user', 'semester')

    return render(request, 'office/schedule.html', {
        'staff': staff,
        'offerings': offerings,
    })


@login_required
def stipend_queue_view(request):
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('office:dashboard')


@login_required
def disburse_stipend(request, disbursement_id=None):
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('office:dashboard')
