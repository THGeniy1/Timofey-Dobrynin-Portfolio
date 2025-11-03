import os

from datetime import timedelta
from pathlib import Path

from os import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    'studiumspace.ru',
    'www.studiumspace.ru',
]

BASE_URL = "https://studiumspace.ru"

SECURE_SSL_REDIRECT = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Cookies
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SAMESITE = 'Lax'

# CSRF and CORS
CSRF_TRUSTED_ORIGINS = [
    'https://studiumspace.ru',
    'https://www.studiumspace.ru',
]
CORS_ALLOWED_ORIGINS = [
    'https://studiumspace.ru',
    'https://www.studiumspace.ru',
]

# Application definition

INSTALLED_APPS = [
    'daphne',
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'corsheaders',
    'csp',
    'rest_framework',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'authentication.apps.AuthenticationConfig',
    'users',
    'ready_tasks',
    'storage',
    'reports',
    'notifications',
    'feedbacks',
    'jsons',
    'rules',
    'payments',
    'refunds',
    'order_tasks'
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '1000/hour',
        'anon': '1000/day',
    }
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Настройки безопасности
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

CONTENT_SECURITY_POLICY = {
    'REPORT_ONLY': False,
    'DIRECTIVES': {
        'default-src': ("'self'",),
        'script-src': (
            "'self'",
            "https://cdnjs.cloudflare.com",
            "https://5486420d-052f-44cd-923d-9b6758f3e9df.selstorage.ru",
        ),
        'style-src': (
            "'self'",
            "https://cdnjs.cloudflare.com",
            "https://5486420d-052f-44cd-923d-9b6758f3e9df.selstorage.ru",
        ),
        'img-src': (
            "'self'",
            'data:',
            'studiumspace.ru',
            'www.studiumspace.ru',
            'https://5486420d-052f-44cd-923d-9b6758f3e9df.selstorage.ru',
        ),
        'connect-src': ("'self'", 'api.studiumspace.ru'),
        'font-src': ("'self'", 'https://cdnjs.cloudflare.com'),
        'frame-ancestors': ("'none'",),
        'object-src': ("'none'",),
        'base-uri': ("'self'",),
        'form-action': ("'self'",),
        'frame-src': ("'none'",),
        'media-src': ("'self'",),
        'worker-src': ("'self'",),
        'manifest-src': ("'self'",),
        'prefetch-src': ("'self'",),
        'upgrade-insecure-requests': True,
    },
}

ROOT_URLCONF = 'studium_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'loaders': [
                ('django.template.loaders.cached.Loader', [
                    'django.template.loaders.filesystem.Loader',
                    'django.template.loaders.app_directories.Loader',
                ]),
            ],
        },
    },
]

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),

        'DISABLE_SERVER_SIDE_CURSORS': True,

        'OPTIONS': {
            'sslmode': 'verify-full',
            'sslrootcert': os.environ.get('DB_SSL_PATH'),
        }
    }
}

ADMINS = (('Admin', 'dobrynya.201@mail.ru'),)

AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_KEY')

AWS_PRIVATE_STORAGE_BUCKET_NAME = environ.get('PRIVATE_BUCKET_NAME')
AWS_PRIVATE_ENDPOINT_URL = environ.get('PRIVATE_ENDPOINT_URL')

AWS_PUBLIC_STORAGE_BUCKET_NAME = environ.get('PUBLIC_BUCKET_NAME')
AWS_PUBLIC_ENDPOINT_URL = environ.get('PUBLIC_ENDPOINT_URL')
AWS_PUBLIC_STORAGE_DOMAIN = os.environ.get('PUBLIC_STORAGE_DOMAIN')

AWS_QUERYSTRING_AUTH = False
AWS_DEFAULT_ACL = 'public-read'

AWS_REGION_NAME = os.environ.get('AWS_REGION_NAME', 'ru-7')

# Кэширование в браузере и CDN
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=86400, s-maxage=86400, must-revalidate',
}

#Для статики
AWS_LOCATION = 'static'
AWS_STORAGE_BUCKET_NAME = environ.get('PUBLIC_BUCKET_NAME')
AWS_S3_ENDPOINT_URL = os.environ.get('PUBLIC_ENDPOINT_URL')

STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_S3_CUSTOM_DOMAIN = os.environ.get('PUBLIC_STORAGE_DOMAIN')

REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = os.environ.get('REDIS_PORT', '6379')

REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"

CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

AUTH_USER_MODEL = 'authentication.CustomUser'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Payments
TINKOFF_TERMINAL_KEY = environ.get('TerminalKey')
TINKOFF_PASSWORD = environ.get('TerminalPassword')
TINKOFF_API_URL = "https://securepay.tinkoff.ru/v2"
# Для тестов: https://rest-api-test.tinkoff.ru/v2

SELECTEL_SERVICE_USER_USERNAME = environ.get('SELECTEL_SERVICE_USER_USERNAME')
SELECTEL_SERVICE_USER_PASSWORD = environ.get('SELECTEL_SERVICE_USER_PASSWORD')
SELECTEL_ACCOUNT_ID = environ.get('SELECTEL_ACCOUNT_ID')
SELECTEL_PROJECT_NAME = environ.get('SELECTEL_PROJECT_NAME')

# ATOL Online v4 (TEST ENV)

ATOL_BASE_URL = environ.get('ATOL_BASE_URL', 'https://testonline.atol.ru/possystem/v4')
ATOL_LOGIN = environ.get('ATOL_LOGIN', 'v4-online-atol-ru')
ATOL_PASSWORD = environ.get('ATOL_PASSWORD', 'iGFFuihss')
ATOL_GROUP_CODE = environ.get('ATOL_GROUP_CODE', 'v4-online-atol-ru_4179')
ATOL_PAYMENT_ADDRESS = BASE_URL

ATOL_PAYMENT_TYPE = 1 
ATOL_SNO = environ.get('ATOL_SNO', 'usn_income')
ATOL_COMPANY_INN = environ.get('ATOL_COMPANY_INN', '5544332219')

ATOL_COMPANY_EMAIL = environ.get('ATOL_COMPANY_EMAIL', 'studiuminfo@yandex.ru') 
ATOL_AGENT_TYPE = environ.get('ATOL_AGENT_TYPE', 'commission_agent') 
ATOL_CALLBACK_URL = f'{BASE_URL}/api/payments/atol_callback/'   

JUMP_FINANCE_API_TOKEN = environ.get('JUMP_FINANCE_API_TOKEN')
JUMP_FINANCE_API_URL = 'https://api.jump.finance'

# Telegram бот для уведомлений
TELEGRAM_BOT_TOKEN = "*"
TELEGRAM_ADMIN_CHAT_ID = '*'

# Email для уведомлений
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = environ.get('EMAIL_HOST')
EMAIL_PORT = environ.get('EMAIL_PORT')
EMAIL_HOST_USER = environ.get('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = environ.get('EMAIL_HOST_PASSWORD')
EMAIL_USE_SSL = True

DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
SERVER_EMAIL = EMAIL_HOST_USER
EMAIL_ADMIN = EMAIL_HOST_USER

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True
USE_L10N = True
USE_TZ = True

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'AUTH_HEADER_TYPES': ('Bearer',),
    'SIGNING_KEY': SECRET_KEY,
}

ASGI_APPLICATION = "studium_backend.asgi.application"

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [(REDIS_HOST, int(REDIS_PORT))],
        },
    },
}


WSGI_APPLICATION = 'studium_backend.wsgi.application'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{levelname}] {asctime} {name}:{lineno} {message}',
            'style': '{',
        },
        'simple': {
            'format': '[{levelname}] {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'django.log',
            'maxBytes': 5 * 1024 * 1024,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'class': 'django.utils.log.AdminEmailHandler',
            'level': 'ERROR',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['mail_admins', 'file'],
            'level': 'ERROR',
            'propagate': False,
        },
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
        },
    },
}