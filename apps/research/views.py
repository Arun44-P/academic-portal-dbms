import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from apps.accounts.models import InstructorProfile
from apps.academics.models import CourseOffering, Enrollment
from apps.research.models import (
    ResearchProject,
    ResearchJunior,
    StipendDisbursement,
    ResearchPublication,
)


@login_required
def faculty_dashboard(request):
    if request.user.role != 'TEACHER':
        messages.error(request, "Access restricted to Faculty members.")
        return redirect('accounts:role_dispatch')

    instructor = get_object_or_404(InstructorProfile, user=request.user)

    # Academic Wing: Courses & Offerings
    offerings = CourseOffering.objects.filter(instructor=instructor).select_related('course', 'semester')
    
    # Research Wing: Projects
    pi_projects = ResearchProject.objects.filter(pi=instructor).prefetch_related('juniors')
    co_pi_projects = ResearchProject.objects.filter(co_investigators__instructor=instructor)

    # Research Juniors
    juniors = ResearchJunior.objects.filter(project__pi=instructor).select_related('project')

    # Stipends Awaiting PI Approval
    pending_stipends = StipendDisbursement.objects.filter(
        junior__project__pi=instructor,
        payment_status='PENDING_PI_APPROVAL'
    ).select_related('junior', 'junior__project')

    # Recent Publications
    publications = ResearchPublication.objects.filter(instructor=instructor).order_by('-publication_date')

    return render(request, 'teacher/dashboard.html', {
        'instructor': instructor,
        'teacher': instructor,
        'offerings': offerings,
        'pi_projects': pi_projects,
        'co_pi_projects': co_pi_projects,
        'juniors': juniors,
        'pending_stipends': pending_stipends,
        'publications': publications,
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
def approve_stipend(request, disbursement_id):
    if request.user.role != 'TEACHER':
        messages.error(request, "Access denied.")
        return redirect('accounts:role_dispatch')

    instructor = get_object_or_404(InstructorProfile, user=request.user)
    stipend = get_object_or_404(
        StipendDisbursement,
        id=disbursement_id,
        junior__project__pi=instructor
    )

    if request.method == 'POST':
        stipend.pi_approved = True
        stipend.pi_approval_date = datetime.date.today()
        stipend.payment_status = 'APPROVED_BY_PI'
        stipend.save()
        messages.success(
            request,
            f"Stipend of ₹{stipend.amount} for {stipend.junior.full_name} ({stipend.disbursement_month}/{stipend.disbursement_year}) approved and forwarded to Research Office Accounts!"
        )

    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER') or 'faculty:dashboard'
    return redirect(next_url)


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
    if request.user.role != 'TEACHER':
        messages.error(request, "Access restricted to Faculty members.")
        return redirect('accounts:role_dispatch')

    instructor = get_object_or_404(InstructorProfile, user=request.user)
    pi_projects = ResearchProject.objects.filter(pi=instructor).prefetch_related('juniors', 'co_investigators__instructor__user')
    co_pi_projects = ResearchProject.objects.filter(co_investigators__instructor=instructor).select_related('pi__user')

    return render(request, 'teacher/research_projects.html', {
        'instructor': instructor,
        'pi_projects': pi_projects,
        'co_pi_projects': co_pi_projects,
    })


@login_required
def research_juniors_view(request):
    if request.user.role != 'TEACHER':
        messages.error(request, "Access restricted to Faculty members.")
        return redirect('accounts:role_dispatch')

    instructor = get_object_or_404(InstructorProfile, user=request.user)
    juniors = ResearchJunior.objects.filter(project__pi=instructor).select_related('project', 'student__user')
    pending_stipends = StipendDisbursement.objects.filter(
        junior__project__pi=instructor,
        payment_status='PENDING_PI_APPROVAL'
    ).select_related('junior', 'junior__project')
    all_stipends = StipendDisbursement.objects.filter(
        junior__project__pi=instructor
    ).select_related('junior', 'junior__project').order_by('-disbursement_year', '-disbursement_month')

    return render(request, 'teacher/research_juniors.html', {
        'instructor': instructor,
        'juniors': juniors,
        'pending_stipends': pending_stipends,
        'all_stipends': all_stipends,
    })


@login_required
def publications_view(request):
    if request.user.role != 'TEACHER':
        messages.error(request, "Access restricted to Faculty members.")
        return redirect('accounts:role_dispatch')

    instructor = get_object_or_404(InstructorProfile, user=request.user)
    projects = ResearchProject.objects.filter(pi=instructor)

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        venue_name = request.POST.get('venue_name', '').strip()
        pub_type = request.POST.get('publication_type', 'JOURNAL')
        pub_date_str = request.POST.get('publication_date')
        doi = request.POST.get('doi_or_url', '').strip()
        impact = request.POST.get('impact_factor') or 0.0
        project_id = request.POST.get('project_id')

        proj = projects.filter(id=project_id).first() if project_id else None
        pub_date = datetime.date.today()
        if pub_date_str:
            try:
                pub_date = datetime.date.fromisoformat(pub_date_str)
            except Exception:
                pass

        if title and venue_name:
            ResearchPublication.objects.create(
                instructor=instructor,
                project=proj,
                title=title,
                venue_name=venue_name,
                publication_type=pub_type,
                publication_date=pub_date,
                doi_or_url=doi,
                impact_factor=float(impact),
            )
            messages.success(request, f"Publication '{title}' indexed successfully!")
            return redirect('faculty:publications')

    publications = ResearchPublication.objects.filter(instructor=instructor).order_by('-publication_date')

    return render(request, 'teacher/publications.html', {
        'instructor': instructor,
        'publications': publications,
        'projects': projects,
    })
