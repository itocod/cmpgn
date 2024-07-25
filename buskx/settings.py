import os
from pathlib import Path
from dotenv import load_dotenv
import environ
import dj_database_url


env = environ.Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file
env_file = BASE_DIR / '.env'
load_dotenv(env_file)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG') == 'False'

ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '').split(',')


# Application definition

INSTALLED_APPS = [
    'tinymce',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'accounts',
    'crispy_forms',
    'main.apps.MainConfig',
    'django.contrib.sites',  # Add the sites framework if needed
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
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
    # Add the following line for allauth middleware
    'allauth.account.middleware.AccountMiddleware',
    'buskx.middlewares.LegalLinksMiddleware',
]

ROOT_URLCONF = 'buskx.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'accounts/templates'),
           # os.path.join(BASE_DIR, 'your_app2/templates'),
            # Add other app template directories if needed
        ],
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

WSGI_APPLICATION = 'buskx.wsgi.application'



# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
  
]

#postgresql database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}




# Internationalization
# https://docs.djangoproject.com/en/5.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Default primary key field type
# https://docs.djangoproject.com/en/5.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Define the path where static files will be collected
STATIC_URL = '/static/'
# Define the directory where collected static files will be stored
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Add the directories where Django should look for static files
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'accounts/static'),
    # os.path.join(BASE_DIR, 'your_app2/static'),
    # Add other app static directories if needed
]





# Heroku settings
# Whitenoise configuration for serving static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'



MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')




AUTHENTICATION_BACKENDS = [
    # other authentication backends
    'allauth.account.auth_backends.AuthenticationBackend',
]

SITE_ID = 1  # Required for django-allauth

SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {
            'access_type': 'online',
        },
        'APP': {
            'client_id': os.getenv('SOCIALACCOUNT_GOOGLE_CLIENT_ID'),
            'secret': os.getenv('SOCIALACCOUNT_GOOGLE_SECRET'),
            'key': ''
        }
    }
}


# settings.py
AUTH_PASSWORD_VALIDATORS = [
    # ... your existing validators ...
    {
        'NAME': 'accounts.validators.AnyPasswordValidator',
    },
]



# Additional settings to ensure everything works as expected
ACCOUNT_EMAIL_VERIFICATION = os.getenv('ACCOUNT_EMAIL_VERIFICATION')
ACCOUNT_EMAIL_REQUIRED = os.getenv('ACCOUNT_EMAIL_REQUIRED') == 'True'

PRIVACY_POLICY_LINK = os.getenv('PRIVACY_POLICY_LINK')
TERMS_OF_SERVICE_LINK = os.getenv('TERMS_OF_SERVICE_LINK')

# Email settings for password reset using Gmail
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND')
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT'))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')

CRISPY_TEMPLATE_PACK = 'bootstrap4'

AUTH_PASSWORD_VALIDATORS.append({
    'NAME': 'accounts.validators.AnyPasswordValidator',
})

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

# Increase the maximum size of request data that can be stored in memory
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10 MB (increase as needed)

# Redirect URLs
LOGIN_REDIRECT_URL = '/rallynex-logo/'
LOGOUT_REDIRECT_URL = 'index'
