import os.path

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

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

    's3file',
    'tests.testapp',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)


SECRET_KEY = 'SuperSecretKey'
STATIC_URL = '/static/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

SITE_ID = 1
ROOT_URLCONF = 'tests.testapp.urls'

TEMPLATE_DIRS = (
    os.path.join(BASE_DIR, "templates"),
)

USE_L10N = True

AWS_ACCESS_KEY_ID = 'testaccessid'
AWS_S3_CUSTOM_DOMAIN = 'localhost:8081'
AWS_SECRET_ACCESS_KEY = 'supersecretkey'
AWS_STORAGE_BUCKET_NAME = 'test-bucket'
