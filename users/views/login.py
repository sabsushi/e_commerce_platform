from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        if not username or not password:
            return render(request, 'users/login.html', {'error': 'Preenche todos os campos.'})

        user = authenticate(request, username=username, password=password)

        if user is None:
            return render(request, 'users/login.html', {'error': 'Username ou password incorretos.', 'username': username})

        login(request, user)
        return redirect('profile')

    return render(request, 'users/login.html')