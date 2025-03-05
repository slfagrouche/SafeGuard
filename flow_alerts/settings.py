import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
DEBUG = os.getenv('DJANGO_DEBUG', 'False') == 'True'

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Media files configuration
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
DEBUG = True


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'incidents',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'flow_alerts.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'flow_alerts.wsgi.application'

# AWS Configuration with validation
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
if not AWS_ACCESS_KEY_ID:
    raise ValueError("AWS_ACCESS_KEY_ID must be set in environment variables")

AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
if not AWS_SECRET_ACCESS_KEY:
    raise ValueError("AWS_SECRET_ACCESS_KEY must be set in environment variables")

AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
AWS_STORAGE_BUCKET_NAME = os.getenv('AWS_STORAGE_BUCKET_NAME')
if not AWS_STORAGE_BUCKET_NAME:
    raise ValueError("AWS_STORAGE_BUCKET_NAME must be set in environment variables")

# S3 Security Settings
AWS_S3_OBJECT_PARAMETERS = {
    'CacheControl': 'max-age=3600',  # 1 hour cache
}
AWS_DEFAULT_ACL = 'private'  # Keep S3 objects private, access through presigned URLs

# DynamoDB table names
DYNAMODB_INCIDENTS_TABLE = 'Incidents'
DYNAMODB_SUBSCRIBERS_TABLE = 'Subscribers'

# SNS Configuration
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN')
if not SNS_TOPIC_ARN:
    raise ValueError("SNS_TOPIC_ARN must be set in environment variables")

# Keep this for Django admin and auth functionality
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
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
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# File Upload Settings
DATA_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB in bytes
FILE_UPLOAD_MAX_MEMORY_SIZE = 10485760  # 10MB in bytes
