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

    return redirect('faculty:dashboard')
