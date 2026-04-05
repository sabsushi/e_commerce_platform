from django.shortcuts import render
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


@login_required(login_url='login')
def profile_view(request):
    profile = request.user.profile
    context = {
        'username': request.user.username,
        'email':    request.user.email,
        'role':     profile.role,
        'bio':      profile.bio,
    }

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'update_profile':
            email = request.POST.get('email', '').strip()
            bio = request.POST.get('bio', '').strip()
            if email:
                request.user.email = email
                request.user.save()
            profile.bio = bio
            profile.save()
            context['email'] = request.user.email
            context['bio'] = profile.bio
            context['success'] = 'Profile updated successfully!'

        elif action == 'change_password':
            old_password = request.POST.get('old_password')
            new_password = request.POST.get('new_password')

            if not request.user.check_password(old_password):
                context['error_password'] = 'Old password is incorrect.'
            else:
                try:
                    validate_password(new_password, request.user)
                except ValidationError as e:
                    context['error_password'] = ' '.join(e.messages)
                    return render(request, 'users/profile.html', context)
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                context['success_password'] = 'Password changed successfully!'

        context['email'] = request.user.email

    return render(request, 'users/profile.html', context)
