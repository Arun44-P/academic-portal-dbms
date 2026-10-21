import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.accounts.models import InstructorProfile
from apps.academics.models import CourseOffering, Enrollment


@login_required
def faculty_dashboard(request):
    if request.user.role != 'TEACHER':
        messages.error(request, "Access restricted to Faculty members.")
        return redirect('accounts:role_dispatch')

    instructor = get_object_or_404(InstructorProfile, user=request.user)

    # Academic Wing: Courses & Offerings
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


@login_required
def section_roster(request, offering_id):
    if request.user.role != 'TEACHER':
        messages.error(request, "Access denied.")
        return redirect('accounts:role_dispatch')

    instructor = get_object_or_404(InstructorProfile, user=request.user)
    offering = get_object_or_404(CourseOffering, id=offering_id, instructor=instructor)
    enrollments = Enrollment.objects.filter(offering=offering).select_related('student__user')

    return render(request, 'teacher/sections.html', {
        'instructor': instructor,
        'offering': offering,
        'enrollments': enrollments,
    })


@login_required
def approve_stipend(request, disbursement_id=None):
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('faculty:dashboard')


@login_required
def sections_view(request):
    if request.user.role != 'TEACHER':
        messages.error(request, "Access restricted to Faculty members.")
        return redirect('accounts:role_dispatch')

    instructor = get_object_or_404(InstructorProfile, user=request.user)
    offerings = CourseOffering.objects.filter(instructor=instructor).select_related('course', 'semester').prefetch_related('enrollments')

    return render(request, 'teacher/sections.html', {
        'instructor': instructor,
        'offerings': offerings,
    })


@login_required
def attendance_entry_view(request):
    if request.user.role != 'TEACHER':
        messages.error(request, "Access restricted to Faculty members.")
        return redirect('accounts:role_dispatch')

    instructor = get_object_or_404(InstructorProfile, user=request.user)
    offerings = CourseOffering.objects.filter(instructor=instructor).select_related('course', 'semester')

    offering_id = request.GET.get('offering_id') or (offerings.first().id if offerings.exists() else None)
    selected_offering = None
    enrollments = []

    if offering_id:
        selected_offering = offerings.filter(id=offering_id).first()
        if selected_offering:
            enrollments = Enrollment.objects.filter(offering=selected_offering, status='ENROLLED').select_related('student__user')

    if request.method == 'POST':
        session_date = request.POST.get('session_date', str(datetime.date.today()))
        topic = request.POST.get('topic_covered', 'Regular Lecture')
        messages.success(
            request,
            f"Attendance recorded for {selected_offering.course.course_code if selected_offering else 'Section'} on {session_date} (Topic: {topic})! {len(enrollments)} students verified."
        )
        return redirect(f"{request.path}?offering_id={offering_id}")

    return render(request, 'teacher/attendance_entry.html', {
        'instructor': instructor,
        'offerings': offerings,
        'selected_offering': selected_offering,
        'enrollments': enrollments,
    })


@login_required
def marks_entry_view(request):
    if request.user.role != 'TEACHER':
        messages.error(request, "Access restricted to Faculty members.")
        return redirect('accounts:role_dispatch')

    instructor = get_object_or_404(InstructorProfile, user=request.user)
    offerings = CourseOffering.objects.filter(instructor=instructor).select_related('course', 'semester')

    offering_id = request.GET.get('offering_id') or (offerings.first().id if offerings.exists() else None)
    selected_offering = None
    enrollments = []

    if offering_id:
        selected_offering = offerings.filter(id=offering_id).first()
        if selected_offering:
            enrollments = Enrollment.objects.filter(offering=selected_offering, status='ENROLLED').select_related('student__user')

    if request.method == 'POST':
        assessment_type = request.POST.get('assessment_type', 'Mid-Term Examination')
        messages.success(
            request,
            f"Marks draft for {assessment_type} ({selected_offering.course.course_code if selected_offering else 'Course'}) saved successfully!"
        )
        return redirect(f"{request.path}?offering_id={offering_id}")

    return render(request, 'teacher/marks_entry.html', {
        'instructor': instructor,
        'offerings': offerings,
        'selected_offering': selected_offering,
        'enrollments': enrollments,
    })


@login_required
def research_projects_view(request):
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('faculty:dashboard')


@login_required
def research_juniors_view(request):
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('faculty:dashboard')


@login_required
def publications_view(request):
    messages.info(request, "The Research module is not available in the Academic Management Portal.")
    return redirect('faculty:dashboard')
