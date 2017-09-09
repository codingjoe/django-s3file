import os.path
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEBUG = True

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',

    'storages',
    's3file',
    'tests.testapp',
)

DEFAULT_FILE_STORAGE = 'tests.testapp.dummy_storage.DummyS3Boto3Storage'

MIDDLEWARE = MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    's3file.middleware.S3FileMiddleware',
)


SECRET_KEY = 'SuperSecretKey'
STATIC_URL = '/static/'
MEDIA_ROOT = tempfile.mkdtemp()
ROOT_URLCONF = 'tests.testapp.urls'
MEDIA_URL = '/s3/'
SITE_ID = 1

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'APP_DIRS': True,
    },
]

USE_L10N = True

AWS_ACCESS_KEY_ID = 'testaccessid'
AWS_SECRET_ACCESS_KEY = 'supersecretkey'
AWS_STORAGE_BUCKET_NAME = 'test-bucket'
AWS_S3_REGION_NAME = 'eu-central-1'
AWS_S3_SIGNATURE_VERSION = 's3v4'
