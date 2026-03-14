import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY    = os.environ.get('SECRET_KEY', 'dev-key-order_service')
DEBUG         = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'orders', 'cart', 'payments',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF   = 'order_service.urls'
WSGI_APPLICATION = 'order_service.wsgi.application'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

DATABASES = {
    'default': {
        'ENGINE':   'django.db.backends.postgresql',
        'NAME':     os.environ.get('DB_NAME',     'order_db'),
        'USER':     os.environ.get('DB_USER',     'order_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'order_pass_2024'),
        'HOST':     os.environ.get('DB_HOST',     'order_db'),
        'PORT':     os.environ.get('DB_PORT',     '5432'),
        'OPTIONS':  {'connect_timeout': 10},
    }
}

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
    'DEFAULT_RENDERER_CLASSES': ('rest_framework.renderers.JSONRenderer',),
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

LANGUAGE_CODE       = 'en-us'
TIME_ZONE           = 'Asia/Ho_Chi_Minh'
USE_I18N            = True
USE_TZ              = True
DEFAULT_AUTO_FIELD  = 'django.db.models.BigAutoField'
STATIC_URL          = '/static/'
STATIC_ROOT         = BASE_DIR / 'staticfiles'
MEDIA_URL           = '/media/'
MEDIA_ROOT          = BASE_DIR / 'media'

AUTH_SERVICE_URL = os.environ.get('AUTH_SERVICE_URL', 'http://auth_service:8001')
