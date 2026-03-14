import requests
from django.shortcuts import render, redirect
from django.conf import settings

AUTH_URL    = settings.AUTH_SERVICE_URL
CATALOG_URL = getattr(settings, 'CATALOG_SERVICE_URL', 'http://catalog_service:8002')

HEADERS_BASE = {'Host': 'localhost', 'Content-Type': 'application/json'}


def _api(method, base_url, path, **kwargs):
    url     = f"{base_url}/{path.lstrip('/')}"
    headers = kwargs.pop('headers', {})
    headers.setdefault('Host', 'localhost')
    try:
        return requests.request(method, url, headers=headers, timeout=10, **kwargs)
    except Exception:
        return None


def _json(resp):
    if resp is None:
        return {}
    try:
        return resp.json()
    except Exception:
        return {}


def _auth(method, path, **kwargs):
    return _api(method, AUTH_URL, f'/api/auth/{path}', **kwargs)

def _catalog(method, path, **kwargs):
    return _api(method, CATALOG_URL, f'/api/catalog/{path}', **kwargs)

def _bearer(token):
    return {'Authorization': f'Bearer {token}', 'Host': 'localhost'}


# ── Home ──────────────────────────────────────────────────────────────────────
def home(request):
    featured  = _json(_catalog('GET', 'books/?featured=1&page_size=4'))
    bestseller = _json(_catalog('GET', 'books/?bestseller=1&page_size=4'))
    categories = _json(_catalog('GET', 'categories/'))
    return render(request, 'pages/home.html', {
        'user':       request.session.get('user'),
        'featured':   featured.get('results', []),
        'bestsellers': bestseller.get('results', []),
        'categories': categories if isinstance(categories, list) else [],
    })


# ── Catalogue ─────────────────────────────────────────────────────────────────
def catalogue(request):
    params = {k: v for k, v in request.GET.items() if v}
    qs     = '&'.join(f'{k}={v}' for k, v in params.items())
    books_resp  = _json(_catalog('GET', f'books/?{qs}'))
    categories  = _json(_catalog('GET', 'categories/'))
    authors     = _json(_catalog('GET', 'authors/?ordering=name'))
    return render(request, 'pages/catalogue.html', {
        'user':       request.session.get('user'),
        'books':      books_resp.get('results', []),
        'pagination': {
            'count':    books_resp.get('count', 0),
            'next':     books_resp.get('next'),
            'previous': books_resp.get('previous'),
            'page':     int(request.GET.get('page', 1)),
        },
        'categories': categories if isinstance(categories, list) else [],
        'authors':    authors.get('results', []) if isinstance(authors, dict) else [],
        'filters':    params,
    })


# ── Book Detail ───────────────────────────────────────────────────────────────
def book_detail(request, slug):
    book = _json(_catalog('GET', f'books/{slug}/'))
    if not book or book.get('error'):
        return render(request, 'pages/404.html', status=404)
    return render(request, 'pages/book_detail.html', {
        'user': request.session.get('user'),
        'book': book,
    })


# ── Book Upload (seller) ──────────────────────────────────────────────────────
def book_upload(request):
    access = request.session.get('access_token')
    user   = request.session.get('user', {})
    roles  = user.get('roles', [])

    if not access:
        return redirect('login')
    if 'seller' not in roles and 'admin' not in roles:
        return render(request, 'pages/403.html', status=403)

    authors    = _json(_catalog('GET', 'authors/?ordering=name'))
    categories = _json(_catalog('GET', 'categories/'))
    publishers = _json(_catalog('GET', 'publishers/'))

    context = {
        'user':       user,
        'authors':    authors.get('results', []) if isinstance(authors, dict) else [],
        'categories': categories if isinstance(categories, list) else [],
        'publishers': publishers.get('results', []) if isinstance(publishers, dict) else [],
    }

    if request.method == 'POST':
        # Multipart upload (có file ảnh bìa)
        files = {}
        if 'cover_image' in request.FILES:
            files['cover_image'] = request.FILES['cover_image']

        form_data = {
            'title':          request.POST.get('title', ''),
            'subtitle':       request.POST.get('subtitle', ''),
            'isbn':           request.POST.get('isbn', ''),
            'description':    request.POST.get('description', ''),
            'pages':          request.POST.get('pages', ''),
            'language':       request.POST.get('language', 'vi'),
            'book_format':    request.POST.get('book_format', 'paperback'),
            'publish_date':   request.POST.get('publish_date', ''),
            'stock_quantity': request.POST.get('stock_quantity', 0),
            'author_ids':     request.POST.get('author_ids', ''),
            'category_ids':   request.POST.get('category_ids', ''),
            'sale_price':     request.POST.get('sale_price', ''),
            'original_price': request.POST.get('original_price', ''),
            'publisher':      request.POST.get('publisher', ''),
            'shop_id':        request.POST.get('shop_id', '1'),
        }

        headers = _bearer(access)
        headers.pop('Content-Type', None)  # Let requests set multipart boundary

        resp = _api('POST', CATALOG_URL, '/api/catalog/books/upload/',
                    data=form_data, files=files if files else None, headers=headers)

        data = _json(resp)
        if resp and resp.status_code == 201:
            return render(request, 'pages/book_upload.html', {
                **context, 'success': True, 'book': data.get('book', {}),
            })
        else:
            context['error']  = data.get('error', 'Đăng sách thất bại.')
            context['errors'] = data.get('errors', {})
            context['form']   = form_data

    return render(request, 'pages/book_upload.html', context)


# ── Auth views (unchanged) ────────────────────────────────────────────────────
def register(request):
    if request.session.get('access_token'):
        return redirect('home')
    if request.method == 'POST':
        payload = {k: request.POST.get(k, '').strip() for k in
                   ['email', 'username', 'first_name', 'last_name', 'password', 'password2']}
        payload['role'] = request.POST.get('role', 'customer')
        resp = _auth('POST', 'register/', json=payload)
        data = _json(resp)
        if resp and resp.status_code == 201:
            request.session['access_token']  = data['tokens']['access']
            request.session['refresh_token'] = data['tokens']['refresh']
            request.session['user']          = data['user']
            return redirect('home')
        return render(request, 'pages/register.html',
                      {'errors': data.get('errors', {}),
                       'error':  data.get('message', 'Đăng ký thất bại.'),
                       'form':   payload})
    return render(request, 'pages/register.html')


def login(request):
    if request.session.get('access_token'):
        return redirect('home')
    if request.method == 'POST':
        payload = {'email': request.POST.get('email', '').strip(),
                   'password': request.POST.get('password', '')}
        resp = _auth('POST', 'login/', json=payload)
        data = _json(resp)
        if resp and resp.status_code == 200:
            request.session['access_token']  = data.get('access', '')
            request.session['refresh_token'] = data.get('refresh', '')
            request.session['user']          = data.get('user', {})
            return redirect('home')
        error = (data.get('detail') or data.get('message') or
                 (data.get('non_field_errors') or [''])[0] or 'Sai thông tin đăng nhập.')
        return render(request, 'pages/login.html',
                      {'error': error, 'form': payload})
    return render(request, 'pages/login.html')


def logout(request):
    refresh = request.session.get('refresh_token')
    access  = request.session.get('access_token')
    if refresh and access:
        _auth('POST', 'logout/', json={'refresh': refresh}, headers=_bearer(access))
    request.session.flush()
    return redirect('login')


def profile(request):
    access = request.session.get('access_token')
    if not access:
        return redirect('login')
    if request.method == 'POST':
        payload = {k: request.POST.get(k, '') for k in
                   ['first_name', 'last_name', 'bio', 'phone']}
        resp = _auth('PATCH', 'profile/', json=payload, headers=_bearer(access))
        if resp and resp.status_code == 200:
            request.session['user'] = _json(resp)
        return redirect('profile')
    resp = _auth('GET', 'profile/', headers=_bearer(access))
    if resp is None or resp.status_code == 401:
        request.session.flush()
        return redirect('login')
    return render(request, 'pages/profile.html',
                  {'user': _json(resp)})
