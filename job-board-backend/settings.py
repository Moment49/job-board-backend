# Django settings for job-board-backend project.
from pathlib import Path
import os
import environ

# Initialise environment variables
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False),
    CORS_ALLOW_ALL_ORIGINS=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# False if not in os.environ because of casting above
DEBUG = env('DEBUG')

# Raises Django's ImproperlyConfigured
# exception if SECRET_KEY not in os.environ
SECRET_KEY = env('SECRET_KEY')

# ALLOWED_HOSTS should be a list of strings
ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=[])



# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'api.apps.ApiConfig',
    'data_pipeline.apps.DataPipelineConfig',
    'drf_yasg',
    'django_celery_beat',
    'sendgrid',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
   
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'api.middlewares.RequestLogMiddleware',
]

ROOT_URLCONF = 'job-board-backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'job-board-backend.wsgi.application'


# Database
DATABASES = {
    # The db() method is an alias for db_url().
    # 'default': {
    #     'ENGINE': 'django.db.backends.postgresql',
    #     'NAME': env('DB_NAME'),
    #     'USER': env('DB_USER'),
    #     'PASSWORD': env('DB_PASSWORD'),
    #     'HOST': env('DB_HOST'),
    #     'PORT': env('DB_PORT'),
    # },

    'default': env.db('SQLITE_URL')
}

# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Media Settings
MEDIA_ROOT =  os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Set the Custom User Model
AUTH_USER_MODEL = "api.CustomUser"

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# CORS_ALLOWED_ORIGINS should be a list of strings
CORS_ALLOWED_ORIGINS = env.list('CORS_ALLOWED_ORIGINS', default=[])
CORS_ALLOW_ALL_ORIGINS = env('CORS_ALLOW_ALL_ORIGINS')  # Enable this only in development environment
CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

# DRF SPECTACULAR FOR SWAGGER DOCS
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    )
}



# ACTS AS CACHE AND BROKER FOR CELERY TASKS
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": env('CACHE_URL'),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    },
}


# CELERY settings - This is the message broker that will be used to send and receive messages from the celery worker
CELERY_BROKER_URL = env("CELERY_BROKER_URL")
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND")

# EMAIL SERVICE CONFIGURATION
EMAIL_BACKEND = "sendgrid_backend.SendgridBackend"
SENDGRID_API_KEY = env("SENDGRID_API_KEY")
SENDGRID_SANDBOX_MODE_IN_DEBUG = False
DEFAULT_FROM_EMAIL= env('DEFAULT_FROM_EMAIL') 


# SYSTEM USER DETAILS
SYSTEM_USER_EMAIL = env('SYSTEM_USER_EMAIL')


# LOGGER SETTINGS
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {name} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file_requests_info': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/requests.log'),
            'formatter': 'simple',
        },
        'file_models_info': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/models.log'),
            'formatter': 'simple',
        },
        'file_tasks': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/tasks.log'),
            'formatter': 'simple',
        },
        'file_app': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/app.log'),
            'formatter': 'simple',
        },
         'file_data_pipeline': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/data_pipeline.log'),
            'formatter': 'simple',
        },
        'file_errors': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, 'logs/errors.log'),
            'formatter': 'simple',
        },
         'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },

    'root': {
        'handlers': [],
        'level': 'INFO',
    },

    'loggers': {
         'django': {
            'handlers': [],
            'level': 'DEBUG',
            'propagate': True,
        },
        'data_pipeline.utils.etl_process': {
            'handlers': ['file_data_pipeline', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'api.tasks': {
            'handlers': ['file_tasks', 'console'],
            'level': 'INFO',
            'propagate': False,
        },

        'api.models': {
            'handlers': ['file_models_info'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'api.middlewares': {
            'handlers': ['file_requests_info', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
        'api.views': {
            'handlers': ['file_app', 'file_errors'],
            'level': 'INFO',
            'propagate': True,
        }
    },
}


from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=120),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    'SLIDING_TOKEN_LIFETIME': timedelta(days=30),
    'SLIDING_TOKEN_REFRESH_LIFETIME_LATE_USER': timedelta(days=1),
    'SLIDING_TOKEN_LIFETIME_LATE_USER': timedelta(days=30),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True
}

# CORS Setup
CORS_ALLOW_HEADERS = (
    "accept",
    "authorization",
    "content-type",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
)

CORS_ALLOWED_ORIGINS = [
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]
CSRF_TRUSTED_ORIGINS = [
      "http://127.0.0.1:8000",
]

CORS_ALLOW_METHODS = (
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
)

IP_GEOLOCATION_SETTINGS = {
    'BACKEND': 'django_ip_geolocation.backends.IPGeolocationAPI',
    'BACKEND_API_KEY': env('GEO_API_KEY'),
    'BACKEND_EXTRA_PARAMS': {},
    'BACKEND_USERNAME': '',
    'RESPONSE_HEADER': 'X-IP-Geolocation',
    'ENABLE_REQUEST_HOOK': True,
    'ENABLE_RESPONSE_HOOK': True,
    'ENABLE_COOKIE': False,
    'FORCE_IP_ADDR': None,
    'USER_CONSENT_VALIDATOR': None
    }