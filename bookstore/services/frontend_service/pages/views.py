import requests
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib import messages

AUTH_URL = settings.AUTH_SERVICE_URL


def _api(method, path, **kwargs):
    url = f"{AUTH_URL}/api/auth/{path}"
    try:
        return requests.request(method, url, timeout=10, **kwargs)
    except requests.exceptions.ConnectionError:
        return None


def home(request):
    user = request.session.get('user')
    return render(request, 'pages/home.html', {'user': user})


def register(request):
    if request.session.get('access_token'):
        return redirect('home')
    if request.method == 'POST':
        payload = {
            'email':      request.POST.get('email', '').strip(),
            'username':   request.POST.get('username', '').strip(),
            'first_name': request.POST.get('first_name', '').strip(),
            'last_name':  request.POST.get('last_name', '').strip(),
            'password':   request.POST.get('password', ''),
            'password2':  request.POST.get('password2', ''),
        }
        resp = _api('POST', 'register/', json=payload)
        if resp is None:
            return render(request, 'pages/register.html',
                          {'error': 'Cannot connect to auth service.', 'form': payload})
        data = resp.json()
        if resp.status_code == 201:
            request.session['access_token']  = data['tokens']['access']
            request.session['refresh_token'] = data['tokens']['refresh']
            request.session['user']          = data['user']
            return redirect('home')
        else:
            return render(request, 'pages/register.html',
                          {'errors': data.get('errors', {}),
                           'error':  data.get('message', 'Registration failed.'),
                           'form':   payload})
    return render(request, 'pages/register.html')


def login(request):
    if request.session.get('access_token'):
        return redirect('home')
    if request.method == 'POST':
        payload = {
            'email':    request.POST.get('email', '').strip(),
            'password': request.POST.get('password', ''),
        }
        resp = _api('POST', 'login/', json=payload)
        if resp is None:
            return render(request, 'pages/login.html',
                          {'error': 'Cannot connect to auth service.', 'form': payload})
        data = resp.json()
        if resp.status_code == 200:
            request.session['access_token']  = data['access']
            request.session['refresh_token'] = data['refresh']
            request.session['user']          = data['user']
            return redirect('home')
        else:
            return render(request, 'pages/login.html',
                          {'error': data.get('detail', data.get('message', 'Invalid credentials.')),
                           'form':  payload})
    return render(request, 'pages/login.html')


def logout(request):
    refresh = request.session.get('refresh_token')
    access  = request.session.get('access_token')
    if refresh and access:
        _api('POST', 'logout/',
             json={'refresh': refresh},
             headers={'Authorization': f'Bearer {access}'})
    request.session.flush()
    return redirect('login')


def profile(request):
    access = request.session.get('access_token')
    if not access:
        return redirect('login')
    headers = {'Authorization': f'Bearer {access}'}
    if request.method == 'POST':
        payload = {
            'first_name': request.POST.get('first_name', ''),
            'last_name':  request.POST.get('last_name', ''),
            'bio':        request.POST.get('bio', ''),
            'phone':      request.POST.get('phone', ''),
        }
        resp = _api('PATCH', 'profile/', json=payload, headers=headers)
        if resp and resp.status_code == 200:
            request.session['user'] = resp.json()
            return redirect('profile')
    resp = _api('GET', 'profile/', headers=headers)
    if resp is None or resp.status_code == 401:
        request.session.flush()
        return redirect('login')
    return render(request, 'pages/profile.html', {'user': resp.json()})
