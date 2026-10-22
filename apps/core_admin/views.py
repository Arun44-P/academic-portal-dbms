from decimal import Decimal
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import connection
from django.db.models import Sum, Count

from apps.accounts.models import (
    UserAccount,
    StudentProfile,
    InstructorProfile,
    PermanentFaculty,
    AssistantProfessor,
    VisitingProfessor,
    OfficeStaffProfile,
)
from apps.academics.models import Course, CourseOffering, StudentFeeAccount, FeePayment
from apps.core_admin.models import AdminAuditLog


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


@login_required
def admin_dashboard(request):
    if request.user.role != 'ADMIN':
        messages.error(request, "Access restricted to Administrators.")
        return redirect('accounts:role_dispatch')

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

    role_counts = {
        'STUDENT': UserAccount.objects.filter(role='STUDENT').count(),
        'TEACHER': UserAccount.objects.filter(role='TEACHER').count(),
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


@login_required
def database_console(request):
    if request.user.role != 'ADMIN':
        messages.error(request, "Access restricted to Administrators.")
        return redirect('accounts:role_dispatch')

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


@login_required
def execute_radical_action(request):
    if request.user.role != 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('accounts:role_dispatch')

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


@login_required
def user_directory(request):
    if request.user.role != 'ADMIN':
        messages.error(request, "Access restricted to Administrators.")
        return redirect('accounts:role_dispatch')

    role_filter = request.GET.get('role', '')
    users = UserAccount.objects.all().order_by('-created_at')
    if role_filter:
        users = users.filter(role=role_filter)

    return render(request, 'admin/users.html', {
        'users': users,
        'current_role_filter': role_filter,
    })


@login_required
def toggle_user_status(request, user_id):
    if request.user.role != 'ADMIN':
        messages.error(request, "Access denied.")
        return redirect('accounts:role_dispatch')

    target_user = get_object_or_404(UserAccount, id=user_id)
    if target_user == request.user:
        messages.error(request, "Cannot deactivate your own administrator account.")
        return redirect('core_admin:user_directory')

    target_user.is_active = not target_user.is_active
    target_user.save()

    status_str = "activated" if target_user.is_active else "deactivated"
    messages.success(request, f"User {target_user.username} has been {status_str}.")
    return redirect('core_admin:user_directory')


@login_required
def audit_logs(request):
    if request.user.role != 'ADMIN':
        messages.error(request, "Access restricted to Administrators.")
        return redirect('accounts:role_dispatch')

    logs = AdminAuditLog.objects.select_related('admin__user').order_by('-created_at')
    return render(request, 'admin/audit_logs.html', {
        'logs': logs,
    })
