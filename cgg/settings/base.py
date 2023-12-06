"""
Django settings for cgg project.

Generated by 'django-admin startproject' using Django 2.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""
import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('CGRATES_GATEWAY_SECRET_KEY',
                       'h7no2l47ur9jx^)2b-mlp@_hckf#*yqvwtbgtys*&zlc=yp(@u')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True if os.getenv(
    'CGRATES_GATEWAY_DEBUG_MODE',
    'True',
) == 'True' else False
ALLOWED_HOSTS = [
    e.strip() for e in os.getenv("CGRATES_GATEWAY_ALLOWED_HOSTS").split(',')
]

# Application definition

INSTALLED_APPS = [
    # Django Modules.
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third Party Modules.
    'rest_framework',
    'rangefilter',

    # CGG Applications.
    'cgg.apps.api_request.apps.APIRequestConfig',
    'cgg.apps.finance.apps.FinanceConfig',
    'cgg.apps.basic.apps.BasicConfig',

    # Health check apps
    'health_check',
    'health_check.db',
    'health_check.cache',
    'health_check.storage',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cgg.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': []
        ,
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

WSGI_APPLICATION = 'cgg.wsgi.application'

# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('CGRATES_GATEWAY_DATABASES_DEFAULT_NAME'),
        'USER': os.getenv('CGRATES_GATEWAY_DATABASES_DEFAULT_USER'),
        'PASSWORD': os.getenv('CGRATES_GATEWAY_DATABASES_DEFAULT_PASSWORD'),
        'HOST': os.getenv('CGRATES_GATEWAY_DATABASES_DEFAULT_HOST'),
        'PORT': os.getenv('CGRATES_GATEWAY_DATABASES_DEFAULT_PORT', 5432),
        'TEST': {
            'NAME': os.getenv('CGRATES_GATEWAY_DATABASES_TEST_DEFAULT_NAME'),
        },
    },
    'log': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': os.getenv('CGRATES_GATEWAY_DATABASES_LOG_NAME'),
        'USER': os.getenv('CGRATES_GATEWAY_DATABASES_LOG_USER'),
        'PASSWORD': os.getenv('CGRATES_GATEWAY_DATABASES_LOG_PASSWORD'),
        'HOST': os.getenv('CGRATES_GATEWAY_DATABASES_LOG_HOST'),
        'PORT': os.getenv('CGRATES_GATEWAY_DATABASES_LOG_PORT', 5432),
        'TEST': {
            'NAME': os.getenv('CGRATES_GATEWAY_DATABASES_TEST_LOG_NAME'),
        },
    },
}
DATABASE_ROUTERS = ['cgg.settings.database_router.DatabaseRouter']

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{os.getenv('CGRATES_GATEWAY_REDIS_HOST')}:"
                    f"{os.getenv('CGRATES_GATEWAY_REDIS_PORT')}/"
                    f"{os.getenv('CGRATES_GATEWAY_CACHE_DATABASE')}",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient"
        },
        "KEY_PREFIX": os.getenv('CGRATES_GATEWAY_CACHE_PREFIX')
    }
}
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'cgg.core.exception_handler.cgg_exception_handler',
    'DATETIME_FORMAT': '%s.%f',
    'DEFAULT_RENDERER_CLASSES': (
        'rest_framework.renderers.JSONRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_jwt.authentication.JSONWebTokenAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.AllowAny',
    ],
    'DEFAULT_PAGINATION_CLASS':
        'rest_framework.pagination.LimitOffsetPagination',
    'PAGE_SIZE': 20,
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation'
                '.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/
LANGUAGE_CODE = 'fa'

LANGUAGES = (
    ('fa', 'Farsi'),
    ('en', 'English'),
)
LOCALE_PATHS = (
    os.path.join(BASE_DIR, 'locale'),
)

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = os.getenv('CGRATES_GATEWAY_STATIC_URL', '/static/')
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, os.getenv(
        'CGRATES_GATEWAY_STATIC_DIRS',
        'staticfiles',
    )),
)

STATIC_ROOT = os.path.join(
    BASE_DIR, os.getenv(
        'CGRATES_GATEWAY_STATIC_ROOT',
        'static',
    ),
)
# To use loggers: logger = logging.getLogger('integrity') or
# logger = logging.getLogger('common')
LOG_PATH = os.path.join(BASE_DIR, 'logs')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %("
                      "message)s",
            'datefmt': "%Y/%m/%d %H:%M:%S"
        },
        'simple': {
            'format': '%(levelname)s %(message)s'
        },
    },
    'handlers': {
        'cgg_backend': {
            'level': 'DEBUG',
            "filename": os.path.join(LOG_PATH, 'backend.log'),
            'formatter': 'verbose',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'D',
            'interval': 1,
        },
        'cgg_common': {
            'level': 'DEBUG',
            "filename": os.path.join(LOG_PATH, 'common.log'),
            'formatter': 'verbose',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'D',
            'interval': 1,
        },
        'cgg_integrity': {
            'level': 'DEBUG',
            "filename": os.path.join(LOG_PATH, 'integrity.log'),
            'formatter': 'verbose',
            'class': 'logging.handlers.TimedRotatingFileHandler',
            'when': 'D',
            'interval': 1,
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['cgg_backend'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['cgg_backend'],
            'level': 'ERROR',
            'propagate': False,
        },
        'common': {
            'handlers': ['cgg_common'],
            'level': 'DEBUG',
        },
        'integrity': {
            'handlers': ['cgg_integrity'],
            'level': 'DEBUG',
        },
    },
}

# CGG related configs
CGG = {
    'AUTH_TOKENS': {
        'TRUNK_IN': os.getenv(
            'CGRATES_GATEWAY_AUTH_TOKENS_TRUNK_IN',
            '5D6ECD803033DD2051A232D8C55348132318399E21064D2C0103935FCEFB1069',
        ),
        'TRUNK_OUT': os.getenv(
            'CGRATES_GATEWAY_AUTH_TOKENS_TRUNK_OUT',
            '5D6ECD803033DD2051A232D8C55348132318399E21064D2C0103935FCEFB1069',
        ),
        'CGRATES_DASHBOARD': os.getenv(
            'CGRATES_GATEWAY_AUTH_TOKENS_DASHBOARD',
            'UHJvY2Vzc0NEUihjZHIgKmVuZ2luZS5DRFJXaXRoQXJnRGlzcGF0Y2hlciwgcsmV',
        ),
        'CGRATES_BASIC_AUTHENTICATION': {
            "USERNAME": os.getenv('CGRATES_BASIC_AUTHENTICATION_USERNAME'),
            "PASSWORD": os.getenv('CGRATES_BASIC_AUTHENTICATION_PASSWORD')
        },
        'MIS_BASIC_AUTHENTICATION': {
            "USERNAME": os.getenv('CGRATES_MIS_AUTHENTICATION_USERNAME'),
            "PASSWORD": os.getenv('CGRATES_MIS_AUTHENTICATION_PASSWORD')
        }
    },
    'BASE_URLS': {
        "CGRATES": os.getenv('CGRATES_GATEWAY_BASE_URLS_CGRATES_SERVICE'),
        "TRUNK_BACKEND": os.getenv(
            'CGRATES_GATEWAY_BASE_URLS_TRUNK_BACKEND',
        ),
        "CGRATES_GATEWAY": os.getenv(
            'CGRATES_GATEWAY_BASE_URLS_CGRATES_GATEWAY',
        ),
        "MIS_SERVICE": os.getenv(
            'CGRATES_MIS_BASE_URL',
        ),
    },
    'RELATIVE_URLS': {
        "TRUNK_BACKEND": {
            "INTERIM_INVOICE_AUTO_PAYED":
                "/ocs/api/notify/interim-invoice-auto-payed/",
            "INTERIM_INVOICE": "/ocs/api/notify/interim-invoice/",
            "PERIODIC_INVOICE": "/ocs/api/notify/periodic-invoice/",
            "POSTPAID_MAX_USAGE": "/ocs/api/notify/postpaid-max-usage/",
            "DUE_DATE": "/ocs/api/notify/due-date/{warning_type}/",
            "PREPAID_EIGHTY_PERCENT":
                "/ocs/api/notify/prepaid-eighty-percent/",
            "PREPAID_MAX_USAGE": "/ocs/api/notify/prepaid-max-usage/",
            "PREPAID_EXPIRED": "/ocs/api/notify/prepaid-expired/",
            "PREPAID_RENEWED": "/ocs/api/notify/prepaid-renewed/",
            "DEALLOCATION": "/ocs/api/notify/deallocation/{warning_type}/",
        }
    },
    'DEFAULT_TENANT': os.getenv('CGRATES_GATEWAY_DEFAULT_TENANT'),
    'SERVICE_TIMEOUT': int(1) if int(os.getenv(
        'CGRATES_GATEWAY_SERVICE_TIMEOUT')) < 1 else int(
        os.getenv('CGRATES_GATEWAY_SERVICE_TIMEOUT')
    ),
    'MAX_CALL_DURATION': int(
        os.getenv('CGRATES_GATEWAY_MAX_CALL_DURATION_IN_SECONDS', 3600)
    ),
    'CACHE_EXPIRY_GLOBAL': int(
        os.getenv('CGRATES_GATEWAY_GLOBAL_CACHE_EXPIRY', 24 * 60 * 60),
    ),
    'CACHE_EXPIRY_OBJECTS': int(
        os.getenv('CGRATES_GATEWAY_OBJECTS_CACHE_EXPIRY', 5 * 60 * 60),
    ),
    'PACKAGE_CODE_PREFIX': os.getenv('CGRATES_PACKAGE_CODE_PREFIX', 'nexfon-'),
    'API_REQUESTS_KEEP_DAYS': int(1) if int(os.getenv(
        'CGRATES_GATEWAY_API_REQUESTS_KEEP_DAYS')) < 1 else int(
        os.getenv('CGRATES_GATEWAY_API_REQUESTS_KEEP_DAYS')
    ),
}

# Celery configs
CELERY_BROKER_URL = f"{os.getenv('CGRATES_GATEWAY_REDIS_HOST')}:" \
                    f"{os.getenv('CGRATES_GATEWAY_REDIS_PORT')}/" \
                    f"{os.getenv('CGRATES_GATEWAY_CELERY_DATABASE')}"
CELERY_RESULT_BACKEND = f"{os.getenv('CGRATES_GATEWAY_REDIS_HOST')}:" \
                        f"{os.getenv('CGRATES_GATEWAY_REDIS_PORT')}/" \
                        f"{os.getenv('CGRATES_GATEWAY_CELERY_DATABASE')}"
CELERY_BROKER_TRANSPORT_OPTIONS = {'visibility_timeout': 18000}
CELERY_RESULT_BACKEND_TRANSPORT_OPTIONS = {'visibility_timeout': 3600}
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'
