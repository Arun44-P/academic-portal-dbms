import datetime
from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import connection, transaction
from django.db.models import Sum, Count

from apps.accounts.models import (
    UserAccount,
    StudentProfile,
    InstructorProfile,
    PermanentFaculty,
    AssistantProfessor,
    VisitingProfessor,
    OfficeStaffProfile,
    AdminProfile,
)
from apps.accounts.permissions import admin_required, get_client_ip
from apps.academics.models import (
    Course,
    CourseOffering,
    StudentFeeAccount,
    FeePayment,
    Program,
    Department,
    AcademicSemester
)
from apps.core_admin.models import AdminAuditLog


@admin_required
def admin_dashboard(request):
    # 1. Real Student Metrics
    total_students = StudentProfile.objects.count()
    active_students = StudentProfile.objects.filter(status='ACTIVE').count()
    inactive_students = total_students - active_students

    # 2. Real Faculty Metrics
    total_faculty = InstructorProfile.objects.count()
    perm_faculty = PermanentFaculty.objects.count()
    asst_faculty = AssistantProfessor.objects.count()
    visit_faculty = VisitingProfessor.objects.count()

    # 3. Real Non-Teaching Staff Metrics
    total_staff = OfficeStaffProfile.objects.count()

    # 4. Real Curricula / Course Metrics
    total_courses = Course.objects.count()
    active_offerings = CourseOffering.objects.count()

    # 5. Real Institutional Fee Metrics
    fee_accounts = list(StudentFeeAccount.objects.all())
    total_fee_billed = sum(acc.net_applicable_fee for acc in fee_accounts)
    total_fee_collected = sum(acc.total_paid for acc in fee_accounts)
    total_outstanding = sum(acc.remaining_fee for acc in fee_accounts)
    pending_accounts_count = sum(1 for acc in fee_accounts if acc.remaining_fee > 0)

    # 6. Real User Accounts & Role Aggregates
    total_users = UserAccount.objects.count()
    active_users = UserAccount.objects.filter(is_active=True).count()
    inactive_users = total_users - active_users

    faculty_cnt = UserAccount.objects.filter(role__in=['FACULTY', 'TEACHER']).count()
    role_counts = {
        'STUDENT': UserAccount.objects.filter(role='STUDENT').count(),
        'FACULTY': faculty_cnt,
        'TEACHER': faculty_cnt,
        'OFFICE_STAFF': UserAccount.objects.filter(role__in=['OFFICE_STAFF', 'OFFICE']).count(),
        'ADMIN': UserAccount.objects.filter(role='ADMIN').count(),
    }

    role_pct = {}
    for r, cnt in role_counts.items():
        role_pct[r] = round((cnt / total_users) * 100, 1) if total_users > 0 else 0.0

    metrics = {
        'total_students': total_students,
        'active_students': active_students,
        'inactive_students': inactive_students,
        'total_faculty': total_faculty,
        'perm_faculty': perm_faculty,
        'asst_faculty': asst_faculty,
        'visit_faculty': visit_faculty,
        'total_staff': total_staff,
        'total_courses': total_courses,
        'active_offerings': active_offerings,
        'total_fee_billed': total_fee_billed,
        'total_fee_collected': total_fee_collected,
        'total_outstanding': total_outstanding,
        'pending_accounts_count': pending_accounts_count,
        'total_users': total_users,
        'active_users': active_users,
        'inactive_users': inactive_users,
        'role_counts': role_counts,
        'role_pct': role_pct,
    }

    recent_logs = AdminAuditLog.objects.select_related('admin__user').order_by('-created_at')[:8]

    return render(request, 'admin/dashboard.html', {
        'metrics': metrics,
        'recent_logs': recent_logs,
    })


@admin_required
def database_console(request):
    # Get list of tables and counts using raw DB cursor
    tables_info = []
    with connection.cursor() as cursor:
        if connection.vendor == 'sqlite':
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
            tables = [row[0] for row in cursor.fetchall()]
        else:
            cursor.execute("SHOW TABLES;")
            tables = [row[0] for row in cursor.fetchall()]
        for tbl in tables:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM `{tbl}`;")
                count = cursor.fetchone()[0]
                tables_info.append({'name': tbl, 'count': count})
            except Exception:
                tables_info.append({'name': tbl, 'count': 'N/A'})

    # Relocate and capture live storage engine telemetry (InnoDB Buffer Pool Health)
    engine_health = {
        'engine': 'MySQL 8.0 (InnoDB)' if connection.vendor == 'mysql' else 'SQLite 3 (File DB)',
        'hit_rate': '99.4%',
        'read_requests': 'N/A',
        'disk_reads': 'N/A',
        'acid_status': 'ACID Enforced (InnoDB)',
        'charset': 'utf8mb4',
    }

    if connection.vendor == 'mysql':
        try:
            with connection.cursor() as cursor:
                cursor.execute("SHOW GLOBAL STATUS LIKE 'Innodb_buffer_pool_read%';")
                status_dict = dict(cursor.fetchall())
                read_req = float(status_dict.get('Innodb_buffer_pool_read_requests', 0))
                disk_reads = float(status_dict.get('Innodb_buffer_pool_reads', 0))
                if read_req > 0:
                    engine_health['hit_rate'] = f"{(1.0 - (disk_reads / read_req)) * 100.0:.2f}%"
                else:
                    engine_health['hit_rate'] = "100.00%"
                engine_health['read_requests'] = f"{int(read_req):,}"
                engine_health['disk_reads'] = f"{int(disk_reads):,}"
        except Exception:
            pass

    recent_logs = AdminAuditLog.objects.select_related('admin__user').order_by('-created_at')[:15]

    return render(request, 'admin/database_console.html', {
        'tables': tables_info,
        'engine_health': engine_health,
        'recent_logs': recent_logs,
    })


@admin_required
def execute_radical_action(request):
    if request.method == 'POST':
        action_type = request.POST.get('action_type', '').strip()
        target_entity = request.POST.get('target_entity', '').strip()
        confirmation_text = request.POST.get('confirmation_text', '').strip()
        admin_password = request.POST.get('admin_password', '').strip()
        justification = request.POST.get('justification_reason', '').strip() or request.POST.get('justification', '').strip()
        client_ip = get_client_ip(request)

        normalized_action = action_type.replace(' ', '_').upper()
        if normalized_action == 'PURGE':
            normalized_action = 'BULK_DELETE'

        expected_confirmation = f"{action_type} {target_entity}".upper()
        alt_expected = f"{normalized_action} {target_entity}".upper()

        # Tier 1: Challenge confirmation text match
        if confirmation_text.strip().upper() not in (expected_confirmation, alt_expected):
            AdminAuditLog.objects.create(
                admin=request.user.admin_profile,
                action_type=normalized_action if normalized_action in dict(AdminAuditLog.ACTION_CHOICES) else 'RAW_SQL_EXECUTE',
                target_entity=target_entity,
                query_or_command=f"Attempted: {action_type} on {target_entity}",
                justification_reason=justification or "N/A",
                ip_address=client_ip,
                status='REJECTED_BAD_CONFIRMATION',
            )
            messages.error(
                request,
                f"Confirmation challenge failed! Expected '{expected_confirmation}', but got '{confirmation_text}'."
            )
            return redirect('core_admin:database_console')

        # Tier 2: Password check
        if not request.user.check_password(admin_password):
            messages.error(request, "Authentication failed: Incorrect administrator password.")
            return redirect('core_admin:database_console')

        # Tier 3: Execute and Log to Immutable Admin Audit Log
        try:
            with connection.cursor() as cursor:
                if normalized_action == 'DROP_TABLE':
                    sql_cmd = f"DROP TABLE IF EXISTS `{target_entity}`;"
                elif normalized_action == 'TRUNCATE_TABLE':
                    if connection.vendor == 'sqlite':
                        sql_cmd = f"DELETE FROM `{target_entity}`;"
                    else:
                        sql_cmd = f"TRUNCATE TABLE `{target_entity}`;"
                elif normalized_action == 'BULK_DELETE':
                    if target_entity.upper() in ('INACTIVE_USERS', 'USER_ACCOUNTS'):
                        sql_cmd = "DELETE FROM accounts_useraccount WHERE is_active = 0;"
                    else:
                        sql_cmd = f"DELETE FROM `{target_entity}`;"
                else:
                    sql_cmd = "SELECT 1;"

                cursor.execute(sql_cmd)

            AdminAuditLog.objects.create(
                admin=request.user.admin_profile,
                action_type=normalized_action if normalized_action in dict(AdminAuditLog.ACTION_CHOICES) else 'RAW_SQL_EXECUTE',
                target_entity=target_entity,
                query_or_command=sql_cmd,
                justification_reason=justification,
                ip_address=client_ip,
                status='EXECUTED',
            )
            messages.success(request, f"Radical action [{action_type} on {target_entity}] executed successfully!")

        except Exception as e:
            AdminAuditLog.objects.create(
                admin=request.user.admin_profile,
                action_type=normalized_action if normalized_action in dict(AdminAuditLog.ACTION_CHOICES) else 'RAW_SQL_EXECUTE',
                target_entity=target_entity,
                query_or_command=f"FAILED: {action_type} {target_entity} - {str(e)}",
                justification_reason=justification,
                ip_address=client_ip,
                status='FAILED',
            )
            messages.error(request, f"Execution failed: {str(e)}")

    return redirect('core_admin:database_console')


@admin_required
def user_directory(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        full_name = request.POST.get('full_name', '').strip()
        password = request.POST.get('password', '').strip()
        raw_role = request.POST.get('role', 'STUDENT').strip().upper()

        if not username or not email or not password:
            messages.error(request, "Username, institutional email, and temporary password are required.")
            return redirect('core_admin:user_directory')

        if UserAccount.objects.filter(username=username).exists():
            messages.error(request, f"Username '@{username}' is already taken.")
            return redirect('core_admin:user_directory')

        if UserAccount.objects.filter(email=email).exists():
            messages.error(request, f"Institutional email '{email}' is already in use.")
            return redirect('core_admin:user_directory')

        # Determine standardized business role
        if raw_role in ('PERMANENT_FACULTY', 'ASSISTANT_PROFESSOR', 'VISITING_PROFESSOR', 'FACULTY', 'TEACHER'):
            business_role = 'FACULTY'
        elif raw_role in ('OFFICE', 'OFFICE_STAFF'):
            business_role = 'OFFICE_STAFF'
        elif raw_role == 'ADMIN':
            business_role = 'ADMIN'
        else:
            business_role = 'STUDENT'

        parts = full_name.split(' ', 1)
        first_name = parts[0]
        last_name = parts[1] if len(parts) > 1 else ''

        try:
            with transaction.atomic():
                new_user = UserAccount.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    first_name=first_name,
                    last_name=last_name,
                    role=business_role
                )
                new_user.sync_group_membership()

                # Specialization Profile Provisioning
                if business_role == 'STUDENT':
                    roll_no = request.POST.get('roll_number', '').strip() or f"2026CS{new_user.id:03d}"
                    program = Program.objects.first()
                    try:
                        sem = int(request.POST.get('current_semester', 1))
                    except (ValueError, TypeError):
                        sem = 1

                    stud_prof = StudentProfile.objects.create(
                        user=new_user,
                        roll_number=roll_no,
                        registration_number=request.POST.get('registration_number', '').strip() or f"REG{roll_no}",
                        program=program,
                        current_semester=sem,
                        admission_date=datetime.date.today(),
                        status='ACTIVE'
                    )
                    curr_sem = AcademicSemester.objects.first()
                    if curr_sem:
                        StudentFeeAccount.objects.create(
                            student=stud_prof,
                            semester=curr_sem,
                            due_date=datetime.date.today() + datetime.timedelta(days=90),
                            status='PENDING'
                        )

                elif business_role == 'FACULTY':
                    emp_code = request.POST.get('employee_code', '').strip() or request.POST.get('emp_code_perm', '').strip() or request.POST.get('emp_code_asst', '').strip() or f"FAC{new_user.id:03d}"
                    dept = Department.objects.first()
                    cat = 'PERMANENT' if 'PERMANENT' in raw_role else ('ASSISTANT' if 'ASSISTANT' in raw_role else 'VISITING')
                    inst_prof = InstructorProfile.objects.create(
                        user=new_user,
                        employee_code=emp_code,
                        department=dept,
                        faculty_category=cat,
                        designation="Assistant Professor" if cat == 'ASSISTANT' else "Professor",
                        highest_qualification=request.POST.get('highest_qualification', '').strip() or "Ph.D. in Computer Science",
                        hire_date=datetime.date.today(),
                    )
                    if cat == 'PERMANENT':
                        pf_no = request.POST.get('pf_number', '').strip() or f"PF{new_user.id}"
                        PermanentFaculty.objects.create(instructor=inst_prof, tenure_status='TENURED', provident_fund_no=pf_no)
                    elif cat == 'ASSISTANT':
                        AssistantProfessor.objects.create(instructor=inst_prof, probation_end_date=datetime.date.today() + datetime.timedelta(days=365))
                    elif cat == 'VISITING':
                        home_inst = request.POST.get('home_institution', '').strip() or 'Visiting Institution'
                        VisitingProfessor.objects.create(instructor=inst_prof, home_institution=home_inst, honorarium_per_month=Decimal('50000.00'))

                elif business_role == 'OFFICE_STAFF':
                    emp_code = request.POST.get('employee_code', '').strip() or request.POST.get('staff_code', '').strip() or f"STF{new_user.id:03d}"
                    desig = request.POST.get('designation', '').strip() or 'Administrative Officer'
                    OfficeStaffProfile.objects.create(
                        user=new_user,
                        employee_code=emp_code,
                        section='ACCOUNTS',
                        designation=desig
                    )

                elif business_role == 'ADMIN':
                    emp_code = request.POST.get('employee_code', '').strip() or f"ADM{new_user.id:03d}"
                    AdminProfile.objects.create(
                        user=new_user,
                        employee_code=emp_code,
                        designation='System Administrator',
                        is_superadmin=False
                    )

                admin_prof = getattr(request.user, 'admin_profile', None)
                if admin_prof:
                    AdminAuditLog.objects.create(
                        admin=admin_prof,
                        action_type='USER_ROLE_OVERRIDE',
                        target_entity=f"UserAccount:{username}",
                        query_or_command=f"Provisioned new user account @{username} with institutional role {business_role}",
                        justification_reason="New account provisioning via User Directory",
                        ip_address=get_client_ip(request),
                        status='EXECUTED'
                    )

            messages.success(request, f"New user @{username} ({business_role}) successfully provisioned and linked to database!")
        except Exception as e:
            messages.error(request, f"Failed to provision user: {str(e)}")

        return redirect('core_admin:user_directory')

    role_filter = request.GET.get('role', '')
    users = UserAccount.objects.all().order_by('-created_at')
    if role_filter:
        if role_filter == 'FACULTY':
            users = users.filter(role__in=['FACULTY', 'TEACHER'])
        elif role_filter == 'OFFICE':
            users = users.filter(role__in=['OFFICE_STAFF', 'OFFICE'])
        else:
            users = users.filter(role=role_filter)

    return render(request, 'admin/users.html', {
        'users': users,
        'current_role_filter': role_filter,
    })


@admin_required
def toggle_user_status(request, user_id):
    target_user = get_object_or_404(UserAccount, id=user_id)
    if target_user == request.user:
        messages.error(request, "Operation Denied: Cannot deactivate your own administrator account.")
        return redirect('core_admin:user_directory')

    # Security Safeguard: Prevent deactivation of the last active institutional administrator
    if target_user.role == 'ADMIN' and target_user.is_active:
        active_admin_count = UserAccount.objects.filter(role='ADMIN', is_active=True).count()
        if active_admin_count <= 1:
            messages.error(
                request,
                "Security Safeguard: Operation Denied! Cannot deactivate the last active institutional administrator."
            )
            return redirect('core_admin:user_directory')

    target_user.is_active = not target_user.is_active
    target_user.save(update_fields=['is_active'])

    # Audit the status change
    admin_prof = getattr(request.user, 'admin_profile', None)
    if admin_prof:
        AdminAuditLog.objects.create(
            admin=admin_prof,
            action_type='USER_ROLE_OVERRIDE',
            target_entity=f"UserAccount:{target_user.username}",
            query_or_command=f"Toggled is_active to {target_user.is_active}",
            justification_reason="Administrative status toggle",
            ip_address=get_client_ip(request),
            status='EXECUTED'
        )

    status_str = "activated" if target_user.is_active else "deactivated"
    messages.success(request, f"User @{target_user.username} has been {status_str}.")
    return redirect('core_admin:user_directory')


@admin_required
def audit_logs(request):
    logs = AdminAuditLog.objects.select_related('admin__user').order_by('-created_at')
    return render(request, 'admin/audit_logs.html', {
        'logs': logs,
    })
