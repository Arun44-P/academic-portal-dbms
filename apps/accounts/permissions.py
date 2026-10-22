"""
Centralized Role-Based Access Control (RBAC) Module
Provides decorators, mixins, and helpers to enforce record-level and role-level security.
"""
from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden


PRIMARY_ROLES = ['ADMIN', 'FACULTY', 'OFFICE_STAFF', 'STUDENT']


def get_client_ip(request):
    """Safely extracts client IP address from HTTP request headers."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')


def normalize_role(role_name):
    """Maps legacy or alias roles to standard business roles."""
    if not role_name:
        return ''
    r = role_name.strip().upper()
    if r == 'TEACHER':
        return 'FACULTY'
    if r == 'OFFICE':
        return 'OFFICE_STAFF'
    return r


def user_has_role(user, allowed_roles):
    """
    Checks whether a user matches any of the allowed roles.
    Inspects user.role and Django group memberships.
    """
    if not user.is_authenticated:
        return False

    # Superuser has administrative privileges
    if user.is_superuser and 'ADMIN' in allowed_roles:
        return True

    user_role = normalize_role(getattr(user, 'role', ''))
    normalized_allowed = [normalize_role(r) for r in allowed_roles]

    if user_role in normalized_allowed:
        return True

    # Check Django Group memberships as secondary verification
    user_groups = set(user.groups.values_list('name', flat=True))
    if any(normalize_role(g) in normalized_allowed for g in user_groups):
        return True

    return False


def role_required(allowed_roles, raise_exception=True):
    """
    Decorator for views that checks whether the logged-in user possesses
    one of the allowed institutional business roles.
    Returns HTTP 403 Forbidden on authorization failure.
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.warning(request, "Please log in with institutional credentials to continue.")
                return redirect('accounts:login')

            if user_has_role(request.user, allowed_roles):
                return view_func(request, *args, **kwargs)

            # User is authenticated, but lacks required role
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('format') == 'json':
                return JsonResponse(
                    {
                        'error': 'Forbidden: Insufficient institutional privileges.',
                        'required_roles': allowed_roles,
                        'current_role': getattr(request.user, 'role', 'UNKNOWN')
                    },
                    status=403
                )

            if raise_exception:
                raise PermissionDenied(
                    f"Access Denied: Your account role ({request.user.role}) is not authorized to access this module."
                )

            messages.error(request, f"Access restricted. Required roles: {', '.join(allowed_roles)}.")
            return redirect('accounts:role_dispatch')

        return _wrapped_view
    return decorator


def student_required(view_func=None, raise_exception=True):
    """Ensures only authenticated Students can access the view."""
    actual_decorator = role_required(['STUDENT'], raise_exception=raise_exception)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def faculty_required(view_func=None, raise_exception=True):
    """Ensures only authenticated Faculty members can access the view."""
    actual_decorator = role_required(['FACULTY', 'TEACHER'], raise_exception=raise_exception)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def office_staff_required(view_func=None, raise_exception=True):
    """Ensures authenticated Office Staff (or Admins where permitted) can access."""
    actual_decorator = role_required(['OFFICE_STAFF', 'ADMIN'], raise_exception=raise_exception)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


def admin_required(view_func=None, raise_exception=True):
    """Ensures only institutional Administrators can access the view."""
    actual_decorator = role_required(['ADMIN'], raise_exception=raise_exception)
    if view_func:
        return actual_decorator(view_func)
    return actual_decorator


class RoleRequiredMixin:
    """Class-based view mixin enforcing institutional RBAC."""
    allowed_roles = []
    raise_exception = True

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('accounts:login')

        if not user_has_role(request.user, self.allowed_roles):
            if self.raise_exception:
                raise PermissionDenied("Access Denied: Insufficient institutional privileges.")
            messages.error(request, "Access restricted.")
            return redirect('accounts:role_dispatch')

        return super().dispatch(request, *args, **kwargs)

