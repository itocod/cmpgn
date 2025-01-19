import os
from pathlib import Path
from dotenv import load_dotenv
import environ

# Load environment variables
env = environ.Env()

# Load .env file
env_file = Path(__file__).resolve().parent.parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

# BASE_DIR configuration
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = env('SECRET_KEY', default='unsafe-secret-key')
DEBUG = env.bool('DEBUG', default=True)
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['www.rallynex.com','localhost', '127.0.0.1'])

# Application definitions
INSTALLED_APPS = [
    'tinymce',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',

    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'storages',
    'accounts',
    'crispy_forms',
    'main.apps.MainConfig',
    'django.contrib.sitemaps',

    
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'buskx.middlewares.LegalLinksMiddleware',
]

ROOT_URLCONF = 'buskx.urls'

# Templates configuration
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'accounts/templates')],
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

# WSGI application
WSGI_APPLICATION = 'buskx.wsgi.application'


# Database configuration
DATABASES = {
    'default': env.db('DATABASE_URL'),
}

CSRF_TRUSTED_ORIGINS = [
    'https://www.rallynex.com',
    'https://rallynex.com',
]



# Authentication and password validators
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'accounts.validators.AnyPasswordValidator',
    },
]

# Localization settings
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# AWS S3 configurations for static and media files
AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY')
AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME')
AWS_S3_REGION_NAME = env('AWS_S3_REGION_NAME', default='us-east-1')
AWS_S3_CUSTOM_DOMAIN = f'{AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com'
AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}

# Static files settings
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
STATIC_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/static/'

# Media files settings
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
MEDIA_URL = f'https://{AWS_S3_CUSTOM_DOMAIN}/media/'

# Email settings
EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT', default=587)
EMAIL_USE_TLS = env.bool('EMAIL_USE_TLS', default=True)
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')

# Authentication backends
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
)

SITE_ID = 1

# Google social account provider settings
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
        'APP': {
            'client_id': env('SOCIALACCOUNT_GOOGLE_CLIENT_ID'),
            'secret': env('SOCIALACCOUNT_GOOGLE_SECRET'),
            'key': ''
        }
    }
}

# Allauth additional settings
ACCOUNT_EMAIL_VERIFICATION = env('ACCOUNT_EMAIL_VERIFICATION', default='none')
ACCOUNT_EMAIL_REQUIRED = env.bool('ACCOUNT_EMAIL_REQUIRED', default=True)
LOGIN_REDIRECT_URL = '/rallynex-logo/'
LOGOUT_REDIRECT_URL = 'index'
SOCIALACCOUNT_LOGIN_ON_GET = True
# Ensure email is required for allauth

# Make sure email verification is handled properly
ACCOUNT_EMAIL_VERIFICATION = 'optional'  # Set this depending on your preference ('mandatory' or 'none')

# Automatically link social accounts to existing email accounts
SOCIALACCOUNT_AUTO_SIGNUP = True

# Connect social accounts to existing users with the same email address
SOCIALACCOUNT_QUERY_EMAIL = True

# Add this to point to your custom adapter
SOCIALACCOUNT_ADAPTER = 'accounts.adapter.CustomSocialAccountAdapter'
# Optional: Require users to provide a username
ACCOUNT_USERNAME_REQUIRED = False





# TinyMCE configuration
TINYMCE_DEFAULT_CONFIG = {
    'height': 360,
    'width': 800,
    'cleanup_on_startup': True,
    'custom_undo_redo_levels': 20,
    'selector': 'textarea',
    'plugins': '''
        textcolor save link image media preview codesample contextmenu
        table code lists fullscreen insertdatetime nonbreaking
        contextmenu directionality searchreplace wordcount visualblocks
        visualchars code fullscreen autolink lists charmap print
        hr anchor pagebreak
        ''',
    'toolbar': '''
        undo redo | styleselect | bold italic | alignleft aligncenter
        alignright alignjustify | bullist numlist outdent indent | link image | codesample
        ''',
    'menubar': True,
    'statusbar': True,
    'contextmenu': True,
}

# File upload size limit
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB

# Legal links settings
PRIVACY_POLICY_LINK = env('PRIVACY_POLICY_LINK')
TERMS_OF_SERVICE_LINK = env('TERMS_OF_SERVICE_LINK')

# Default auto field setting
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# settings.py

SITE_URL = 'https://www.rallynex.com'

# settings.py

SITE_DOMAIN = 'www.rallynex.com'


# PayPal settings
PAYPAL_CLIENT_ID = env('PAYPAL_CLIENT_ID')
PAYPAL_CLIENT_SECRET = env('PAYPAL_CLIENT_SECRET')
PAYPAL_MODE = env('PAYPAL_MODE')  #


SECURE_SSL_REDIRECT = True

