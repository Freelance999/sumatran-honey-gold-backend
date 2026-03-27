import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')

ACCESS_TOKEN_EXPIRY = int(os.getenv('ACCESS_TOKEN_EXPIRY'))
REFRESH_TOKEN_EXPIRY = int(os.getenv('REFRESH_TOKEN_EXPIRY'))
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
WUNDERGROUND_API_KEY = os.getenv('WUNDERGROUND_API_KEY')
STATION_ID = os.getenv('STATION_ID')
OPENWEATHERMAP_API_KEY = os.getenv('OPENWEATHERMAP_API_KEY')
LATITUDE = "-6.234533387561699"
LONGITUDE = "106.7039825516585"
BASE_URL = "https://api.habibie.co.id"

SECRET_KEY = 'django-insecure-rg9*=8_c%!*pjyohj@)7xbyx0xi$ved&#lu0)c)u0pgy#sw(s+'

DEBUG = False

ALLOWED_HOSTS = ["*"]

CSRF_TRUSTED_ORIGINS = [
    "http://api.habibie.co.id",
    "https://api.habibie.co.id",
    "http://habibie.co.id",
    "https://habibie.co.id",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8001",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
    "http://202.10.46.112",
    "http://202.10.46.112:8000",
    "http://202.10.46.112:8001",
    "https://202.10.46.112",
    "https://202.10.46.112:8000",
    "https://202.10.46.112:8001",
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'sumatran_honey_gold_backend',
    'corsheaders',
    'django_crontab',
    'core',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'sumatran_honey_gold_backend.middlewares.middlewares.TokenExpiryMiddleware',
]

CORS_ALLOW_ALL_ORIGINS = True

CORS_ALLOWED_ORIGINS = [
    "http://api.habibie.co.id",
    "https://api.habibie.co.id",
    "http://habibie.co.id",
    "https://habibie.co.id",
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:8001",
    "http://localhost:3000",
    "http://127.0.0.1",
    "http://127.0.0.1:8000",
    "http://127.0.0.1:3000",
    "http://202.10.46.112",
    "http://202.10.46.112:8000",
    "http://202.10.46.112:8001",
    "https://202.10.46.112",
    "https://202.10.46.112:8000",
    "https://202.10.46.112:8001",
]

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'sumatran_honey_gold_backend.middlewares.authentications.BearerTokenAuthentication',
    ],
    'EXCEPTION_HANDLER': 'sumatran_honey_gold_backend.middlewares.exception_handlers.custom_exception_handler',
}

ROOT_URLCONF = 'sumatran_honey_gold_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'sumatran_honey_gold_backend.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
        # 'OPTIONS': {
        #     'init_command': "SET default_storage_engine=INNODB",
        # },
    }
}

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

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Jakarta'

USE_I18N = True

USE_TZ = False

STATIC_URL = 'static/'
STATICFILES_DIRS = (os.path.join(BASE_DIR, 'static'),)
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

STORAGES = {
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'sumatran_honey_gold_backend.CustomUser'

CRONJOBS = [
    ('*/15 * * * *', 'sumatran_honey_gold_backend.cron.store_weather_observation', '>> /tmp/weather_cron.log 2>&1'),
    # Buat Debug (Tiap 1 menit)
    # ('*/1 * * * *', 'sumatran_honey_gold_backend.cron.store_weather_observation', '>> /tmp/weather_cron.log 2>&1'),
]

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = 'Emas Madu Sumatra App <' + EMAIL_HOST_USER + '>'