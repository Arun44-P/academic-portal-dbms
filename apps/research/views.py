import datetime
from decimal import Decimal, InvalidOperation
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.core.exceptions import PermissionDenied

from apps.accounts.models import InstructorProfile
from apps.accounts.permissions import faculty_required, get_client_ip
from apps.academics.models import (
    CourseOffering,
    Enrollment,
    Assessment,
    StudentMark,
    AttendanceRecord,
    MarksAuditLog
)


@faculty_required
def faculty_dashboard(request):
    instructor = get_object_or_404(InstructorProfile, user=request.user)

    # Scoped to assigned offerings only
    offerings = CourseOffering.objects.filter(instructor=instructor).select_related('course', 'semester')
    active_sections_count = offerings.count()
    total_students_count = Enrollment.objects.filter(offering__in=offerings, status='ENROLLED').values('student').distinct().count()

    return render(request, 'teacher/dashboard.html', {
        'instructor': instructor,
        'teacher': instructor,
        'offerings': offerings,
        'active_sections_count': active_sections_count,
        'total_students_count': total_students_count,
    })


@faculty_required
def sections_view(request):
    instructor = get_object_or_404(InstructorProfile, user=request.user)
    offerings = CourseOffering.objects.filter(instructor=instructor).select_related('course', 'semester').prefetch_related('enrollments')

    return render(request, 'teacher/sections.html', {
        'instructor': instructor,
        'offerings': offerings,
    })


@faculty_required
def section_roster(request, offering_id):
    instructor = get_object_or_404(InstructorProfile, user=request.user)
    
    # IDOR Prevention: Ensure offering exists and is officially assigned to requesting faculty
    offering = CourseOffering.objects.filter(id=offering_id).first()
    if not offering:
        messages.error(request, "Section offering not found.")
        return redirect('faculty:sections')

    if offering.instructor != instructor:
        raise PermissionDenied("Access Denied: You are not authorized to view the roster for this course section.")

    enrollments = Enrollment.objects.filter(offering=offering, status='ENROLLED').select_related('student__user', 'student__program')

    return render(request, 'teacher/sections.html', {
        'instructor': instructor,
        'offering': offering,
        'enrollments': enrollments,
    })


@faculty_required
def attendance_entry_view(request):
    instructor = get_object_or_404(InstructorProfile, user=request.user)
    offerings = CourseOffering.objects.filter(instructor=instructor).select_related('course', 'semester')

    offering_param = request.POST.get('offering_id') or request.GET.get('offering_id')
    selected_offering = None

    if offering_param:
        target_offering = CourseOffering.objects.filter(id=offering_param).first()
        if not target_offering:
            messages.error(request, "Selected course offering was not found.")
            return redirect('faculty:attendance_entry')
        
        # IDOR Server-side Check: verify assignment to this faculty
        if target_offering.instructor != instructor:
            raise PermissionDenied("Access Denied: You are not the assigned instructor for this course offering.")
        selected_offering = target_offering
    else:
        selected_offering = offerings.first()

    enrollments = []
    attendance_map = {}
    today_str = str(datetime.date.today())
    session_date_str = request.GET.get('session_date', today_str)

    if selected_offering:
        enrollments = Enrollment.objects.filter(
            offering=selected_offering,
            status='ENROLLED'
        ).select_related('student__user', 'student__program')

        # Load existing attendance records for the selected date
        try:
            parsed_date = datetime.date.fromisoformat(session_date_str)
        except (ValueError, TypeError):
            parsed_date = datetime.date.today()
            session_date_str = str(parsed_date)

        records = AttendanceRecord.objects.filter(
            offering=selected_offering,
            session_date=parsed_date
        )
        attendance_map = {r.student_id: r for r in records}

    if request.method == 'POST':
        if not selected_offering:
            messages.error(request, "No offering selected.")
            return redirect('faculty:attendance_entry')

        date_val = request.POST.get('session_date', today_str)
        topic_val = request.POST.get('topic_covered', 'Regular Class Session').strip()

        try:
            session_date = datetime.date.fromisoformat(date_val)
        except (ValueError, TypeError):
            session_date = datetime.date.today()

        saved_count = 0
        with transaction.atomic():
            for enr in enrollments:
                roll = enr.student.roll_number
                status_key = f"attendance_{roll}"
                remark_key = f"remark_{roll}"

                status_val = request.POST.get(status_key, 'PRESENT')
                if status_val not in ('PRESENT', 'ABSENT', 'LATE', 'EXCUSED'):
                    status_val = 'PRESENT'

                remark_val = request.POST.get(remark_key, '').strip()

                AttendanceRecord.objects.update_or_create(
                    offering=selected_offering,
                    student=enr.student,
                    session_date=session_date,
                    defaults={
                        'status': status_val,
                        'topic_covered': topic_val,
                        'marked_by': instructor,
                    }
                )
                saved_count += 1

        messages.success(
            request,
            f"Attendance recorded successfully for {selected_offering.course.course_code} ({selected_offering.section_name}) on {session_date}. {saved_count} student records updated."
        )
        return redirect(f"{request.path}?offering_id={selected_offering.id}&session_date={session_date}")

    # Build roster with current attendance statuses
    roster_data = []
    present_cnt = 0
    absent_cnt = 0
    for enr in enrollments:
        rec = attendance_map.get(enr.student_id)
        current_status = rec.status if rec else 'PRESENT'
        current_remark = rec.topic_covered if (rec and rec.topic_covered) else ''
        if current_status == 'PRESENT':
            present_cnt += 1
        elif current_status == 'ABSENT':
            absent_cnt += 1

        # Calculate student's overall attendance rate in this offering
        total_sessions = AttendanceRecord.objects.filter(offering=selected_offering, student=enr.student).count()
        attended_sessions = AttendanceRecord.objects.filter(
            offering=selected_offering,
            student=enr.student,
            status__in=['PRESENT', 'LATE', 'EXCUSED']
        ).count()
        overall_pct = round((attended_sessions / total_sessions * 100), 1) if total_sessions > 0 else 100.0

        roster_data.append({
            'enrollment': enr,
            'student': enr.student,
            'current_status': current_status,
            'current_remark': current_remark,
            'overall_pct': overall_pct,
        })

    session_rate = round((present_cnt / len(enrollments) * 100), 1) if enrollments else 0.0

    return render(request, 'teacher/attendance_entry.html', {
        'instructor': instructor,
        'offerings': offerings,
        'selected_offering': selected_offering,
        'roster_data': roster_data,
        'session_date': session_date_str,
        'total_count': len(enrollments),
        'present_cnt': present_cnt,
        'absent_cnt': absent_cnt,
        'session_rate': session_rate,
    })


@faculty_required
def marks_entry_view(request):
    instructor = get_object_or_404(InstructorProfile, user=request.user)
    offerings = CourseOffering.objects.filter(instructor=instructor).select_related('course', 'semester')

    offering_param = request.POST.get('offering_id') or request.GET.get('offering_id')
    selected_offering = None

    if offering_param:
        target_offering = CourseOffering.objects.filter(id=offering_param).first()
        if not target_offering:
            messages.error(request, "Selected course offering was not found.")
            return redirect('faculty:marks_entry')
        
        # IDOR check: verify ownership of offering
        if target_offering.instructor != instructor:
            raise PermissionDenied("Access Denied: You are not authorized to view or record marks for another faculty member's course offering.")
        selected_offering = target_offering
    else:
        selected_offering = offerings.first()

    enrollments = []
    assessments = []

    if selected_offering:
        enrollments = Enrollment.objects.filter(
            offering=selected_offering,
            status='ENROLLED'
        ).select_related('student__user', 'student__program')

        # Ensure standard assessments exist for this offering
        existing_assessments = list(Assessment.objects.filter(offering=selected_offering).order_by('id'))
        if not existing_assessments:
            # Auto-provision standard components
            existing_assessments = [
                Assessment.objects.create(
                    offering=selected_offering,
                    name='Quiz 1',
                    assessment_type='QUIZ',
                    max_marks=Decimal('20.00'),
                    weightage_percent=Decimal('20.00'),
                    is_published=False,
                    created_by=instructor
                ),
                Assessment.objects.create(
                    offering=selected_offering,
                    name='Mid-Term Exam',
                    assessment_type='MID_TERM',
                    max_marks=Decimal('30.00'),
                    weightage_percent=Decimal('30.00'),
                    is_published=False,
                    created_by=instructor
                ),
                Assessment.objects.create(
                    offering=selected_offering,
                    name='End-Term Exam',
                    assessment_type='END_TERM',
                    max_marks=Decimal('50.00'),
                    weightage_percent=Decimal('50.00'),
                    is_published=False,
                    created_by=instructor
                ),
            ]
        assessments = existing_assessments

    if request.method == 'POST':
        if not selected_offering:
            messages.error(request, "No offering selected.")
            return redirect('faculty:marks_entry')

        # Check action: Draft Save vs. Finalize & Publish
        finalize = bool(request.POST.get('finalize'))
        client_ip = get_client_ip(request)

        try:
            with transaction.atomic():
                audit_logs_to_create = []

                for ass in assessments:
                    # Update publication status if finalizing
                    if finalize and not ass.is_published:
                        ass.is_published = True
                        ass.save(update_fields=['is_published', 'updated_at'])

                    for enr in enrollments:
                        roll = enr.student.roll_number
                        mark_key = f"mark_{roll}_{ass.id}"
                        mark_val_str = request.POST.get(mark_key)

                        if mark_val_str is None or mark_val_str.strip() == '':
                            continue

                        try:
                            score = Decimal(str(mark_val_str).strip())
                        except (InvalidOperation, ValueError):
                            messages.error(request, f"Invalid numeric score '{mark_val_str}' for student {roll}.")
                            return redirect(f"{request.path}?offering_id={selected_offering.id}")

                        # Server-side validation against permitted max score
                        if score < Decimal('0.00'):
                            messages.error(request, f"Score for {roll} cannot be negative ({score}).")
                            return redirect(f"{request.path}?offering_id={selected_offering.id}")

                        if score > ass.max_marks:
                            messages.error(
                                request,
                                f"Validation Error: Score {score} for {enr.student.user.get_full_name()} ({roll}) exceeds maximum allowed score of {ass.max_marks} on {ass.name}."
                            )
                            return redirect(f"{request.path}?offering_id={selected_offering.id}")

                        # Fetch existing mark for audit tracking
                        existing_mark = StudentMark.objects.filter(assessment=ass, enrollment=enr).first()

                        if existing_mark:
                            if existing_mark.marks_obtained != score:
                                prev_score = existing_mark.marks_obtained
                                existing_mark.marks_obtained = score
                                existing_mark.entered_by = instructor
                                existing_mark.save()

                                # Record Audit Trail
                                MarksAuditLog.objects.create(
                                    mark=existing_mark,
                                    modified_by=request.user,
                                    previous_score=prev_score,
                                    new_score=score,
                                    change_reason=request.POST.get('change_reason', 'Faculty grade entry'),
                                    ip_address=client_ip
                                )
                        else:
                            new_mark = StudentMark.objects.create(
                                assessment=ass,
                                enrollment=enr,
                                marks_obtained=score,
                                entered_by=instructor
                            )
                            MarksAuditLog.objects.create(
                                mark=new_mark,
                                modified_by=request.user,
                                previous_score=None,
                                new_score=score,
                                change_reason="Initial grade entry",
                                ip_address=client_ip
                            )

            if finalize:
                messages.success(
                    request,
                    f"All marks finalized and published for {selected_offering.course.course_code} ({selected_offering.section_name})! Students can now view their official results."
                )
            else:
                messages.success(
                    request,
                    f"Marks draft saved successfully for {selected_offering.course.course_code}. Draft assessments remain private to faculty."
                )

        except Exception as e:
            messages.error(request, f"Failed to save marks: {str(e)}")

        return redirect(f"{request.path}?offering_id={selected_offering.id}")

    # Build matrix grid data for template rendering
    matrix_rows = []
    # Fetch all existing marks for this offering
    existing_marks_qs = StudentMark.objects.filter(
        assessment__in=assessments,
        enrollment__in=enrollments
    )
    marks_lookup = {(m.enrollment_id, m.assessment_id): m.marks_obtained for m in existing_marks_qs}

    for enr in enrollments:
        student_scores = []
        total_obtained = Decimal('0.00')
        total_max = Decimal('0.00')

        for ass in assessments:
            val = marks_lookup.get((enr.id, ass.id), None)
            if val is not None:
                total_obtained += val
            total_max += ass.max_marks
            student_scores.append({
                'assessment_id': ass.id,
                'assessment_name': ass.name,
                'max_marks': ass.max_marks,
                'score': val if val is not None else '',
            })

        pct = round((total_obtained / total_max * 100), 1) if total_max > 0 else Decimal('0.0')
        grade = 'F'
        grade_badge = 'badge-danger'
        if pct >= 90:
            grade = 'A+'
            grade_badge = 'badge-success'
        elif pct >= 80:
            grade = 'A'
            grade_badge = 'badge-success'
        elif pct >= 70:
            grade = 'B+'
            grade_badge = 'badge-info'
        elif pct >= 60:
            grade = 'B'
            grade_badge = 'badge-warning'
        elif pct >= 50:
            grade = 'C'
            grade_badge = 'badge-warning'

        matrix_rows.append({
            'enrollment': enr,
            'student': enr.student,
            'scores': student_scores,
            'total_obtained': total_obtained,
            'total_max': total_max,
            'percentage': pct,
            'grade': grade,
            'grade_badge': grade_badge,
        })

    all_published = all(ass.is_published for ass in assessments) if assessments else False

    return render(request, 'teacher/marks_entry.html', {
        'instructor': instructor,
        'offerings': offerings,
        'selected_offering': selected_offering,
        'assessments': assessments,
        'matrix_rows': matrix_rows,
        'all_published': all_published,
    })


@faculty_required
def approve_stipend(request, disbursement_id=None):
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('faculty:dashboard')


@faculty_required
def research_projects_view(request):
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('faculty:dashboard')


@faculty_required
def research_juniors_view(request):
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('faculty:dashboard')


@faculty_required
def publications_view(request):
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('faculty:dashboard')
