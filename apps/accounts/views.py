from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.accounts.models import UserAccount


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:role_dispatch')

    if request.method == 'POST':
        identifier = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')

        user = authenticate(request, username=identifier, password=password)
        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('accounts:role_dispatch')
            else:
                messages.error(request, "Your account has been deactivated. Contact the Administrator.")
        else:
            messages.error(request, "Invalid username or password. Please try again.")

    return render(request, 'accounts/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('accounts:login')


@login_required
def role_dispatch_view(request):
    role = getattr(request.user, 'role', '')
    if role == 'ADMIN':
        return redirect('core_admin:dashboard')
    elif role in ('FACULTY', 'TEACHER') or request.user.is_faculty:
        return redirect('faculty:dashboard')
    elif role in ('OFFICE_STAFF', 'OFFICE') or request.user.is_office_staff:
        return redirect('office:dashboard')
    elif role == 'STUDENT' or request.user.is_student:
        return redirect('student:dashboard')
    else:
        messages.error(request, "Unrecognized user role.")
        return redirect('accounts:login')
