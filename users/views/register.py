from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.shortcuts import render, redirect


VALID_ROLES = {choice[0] for choice in __import__('users.models', fromlist=['Profile']).Profile.Role.choices}


def register_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        email    = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        role     = request.POST.get('role', 'buyer')

        if not all([username, email, password]):
            return render(request, 'users/register.html', {'error': 'All fields are required.'})

        if role not in VALID_ROLES:
            return render(request, 'users/register.html', {'error': 'Invalid role selected.'})

        if User.objects.filter(username=username).exists():
            return render(request, 'users/register.html', {'error': 'Username already taken.'})

        if User.objects.filter(email=email).exists():
            return render(request, 'users/register.html', {'error': 'Email already registered.'})

        try:
            validate_password(password)
        except ValidationError as e:
            return render(request, 'users/register.html', {'error': ' '.join(e.messages)})

        user = User.objects.create_user(username=username, email=email, password=password)
        user.profile.role = role
        user.profile.save()

        return redirect('login')

    return render(request, 'users/register.html')
