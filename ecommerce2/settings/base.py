"""
Django settings for ecommerce2 project.
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
#root of project

# Quick-start development settings - unsuitable for production

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'lmasdirkjsckjwekscksjndfle34234nkefnj324hjkw$d90j8$^!nvj41_r'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

EMAIL_HOST = 'smtp.gmail.com'
EMAIL_HOST_USER = 'yourgmail@gmail.com'
EMAIL_HOST_PASSWORD = 'yourpassword'
EMAIL_PORT = 587
EMAIL_USE_TLS = True

BASE_URL = '127.0.0.1:8000'

''' 
If using gmail, you will need to
unlock Captcha to enable Django 
to  send for you:
https://accounts.google.com/displayunlockcaptcha
'''

# Application definition

INSTALLED_APPS = (
    #django app
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    #third party apps
    'crispy_forms',
    'django_filters',
    'pagedown',
    'rest_framework',
    #'registration',
    'storages',
    #my apps
    'accounts',
    'addresses',
    'analytics',
    'billing',
    'carts',
    'delivery',
    'growlers',
    'newsletter',
    'orders',
    'posts',
    'products',
)

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # 'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'ecommerce2.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, "templates")],
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

WSGI_APPLICATION = 'ecommerce2.wsgi.application'


# Database

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Internationalization

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/New_York'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)

STATIC_URL = '/static/'

STATIC_ROOT = os.path.join(os.path.dirname(BASE_DIR), "static_in_env", "static_root")
    
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, "static_in_pro", "our_static"),
)

MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(os.path.dirname(BASE_DIR), "static_in_env", "media_root")


#from ecommerce2.aws.conf import *

#Crispy FORM TAGs SETTINGS
CRISPY_TEMPLATE_PACK = 'bootstrap3'


#Braintree Payments Details
BRAINTREE_PUBLIC = "XXX"
BRAINTREE_PRIVATE = "XXX"
BRAINTREE_MERCHANT_ID = "XXX"
BRAINTREE_ENVIRONEMNT = "Sandbox"

CORS_REPLACE_HTTPS_REFERER      = False
HOST_SCHEME                     = "http://"
SECURE_PROXY_SSL_HEADER         = None
SECURE_SSL_REDIRECT             = False
SESSION_COOKIE_SECURE           = False
CSRF_COOKIE_SECURE              = False
SECURE_HSTS_SECONDS             = None
SECURE_HSTS_INCLUDE_SUBDOMAINS  = False
SECURE_FRAME_DENY               = False


REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend']
}