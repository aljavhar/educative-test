"""
Django settings for EduTest Platform.
Production-ready, API-first configuration.
"""

import os
from datetime import timedelta
import dj_database_url 
import os
from dotenv import load_dotenv
from decouple import config

load_dotenv()

ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Security
SECRET_KEY = config('SECRET_KEY', default='dev-secret-key-change-in-production')
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', "educative-test-production.up.railway.app"] 

CSRF_TRUSTED_ORIGINS = ['https://educative-test-production.up.railway.app']

# ─── Installed Apps ────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'drf_yasg',

    # Our apps
    'users',
    'courses',
    'tests_app',
    'results',
    'ai_generator',
    'web',
]

# ─── Middleware ─────────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',        # CORS — must be before CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eduplatform.urls'

# ─── Login settings ─────────────────────────────────────────────────────────────
LOGIN_URL = '/web/login/'
LOGIN_REDIRECT_URL = '/web/'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'eduplatform.wsgi.application'

# ─── Database (PostgreSQL) ──────────────────────────────────────────────────────
# Uses DATABASE_URL from .env file
# DATABASE_URL = config('DATABASE_URL', default=f'sqlite:///{os.path.join(BASE_DIR, "db.sqlite3")}')

# if DATABASE_URL.startswith('postgres'):
#     import re
#     match = re.match(
#         r'postgres(?:ql)?://(?P<user>[^:]+):(?P<password>[^@]+)@(?P<host>[^:/]+)(?::(?P<port>\d+))?/(?P<name>.+)',
#         DATABASE_URL
#     )
#     if match:
#         DATABASES = {
#             'default': {
#                 'ENGINE': 'django.db.backends.postgresql',
#                 'NAME': match.group('name'),
#                 'USER': match.group('user'),
#                 'PASSWORD': match.group('password'),
#                 'HOST': match.group('host'),
#                 'PORT': match.group('port') or '5432',
#             }
#         }
# else:
#     # Fallback to SQLite for development
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.sqlite3',
#             'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
#         }
#     }

# Railway postgres uchun

POSTGRES_LOCALLY = False
if ENVIRONMENT == 'production' or POSTGRES_LOCALLY == True:
    DATABASES = {'default': dj_database_url.parse(config('DATABASE_URL'))}

# ─── Custom User Model ──────────────────────────────────────────────────────────
AUTH_USER_MODEL = 'users.User'

# ─── Django REST Framework ──────────────────────────────────────────────────────
REST_FRAMEWORK = {
    # JWT is default authentication — perfect for mobile apps
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_PARSER_CLASSES': [
        'rest_framework.parsers.JSONParser',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DATETIME_FORMAT': '%Y-%m-%dT%H:%M:%SZ',
}

# ─── JWT Settings ───────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_ACCESS_TOKEN_LIFETIME', default=60, cast=int)
    ),
    'REFRESH_TOKEN_LIFETIME': timedelta(
        minutes=config('JWT_REFRESH_TOKEN_LIFETIME', default=10080, cast=int)  # 7 days
    ),
    'ROTATE_REFRESH_TOKENS': True,          # New refresh token on each refresh
    'BLACKLIST_AFTER_ROTATION': False,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'TOKEN_TYPE_CLAIM': 'token_type',
    'JTI_CLAIM': 'jti',
}

# ─── CORS ───────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = DEBUG  # Allow all in development
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in config('CORS_ALLOWED_ORIGINS', default='http://localhost:3000').split(',')
]
CORS_ALLOW_CREDENTIALS = True

# ─── Static & Media Files ───────────────────────────────────────────────────────
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# ─── Internationalization ────────────────────────────────────────────────────────
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── Swagger / API Docs ──────────────────────────────────────────────────────────
SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'Enter: Bearer <your-token>',
        }
    },
    'USE_SESSION_AUTH': False,
}
