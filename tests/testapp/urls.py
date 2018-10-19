from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^s3/$',
        views.S3MockView.as_view(), name='s3mock'),
    url(r'^upload/$',
        views.ExampleFormView.as_view(), name='upload'),
]
