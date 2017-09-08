from django.conf.urls import url
from django.views.generic import FormView

from . import forms, views

urlpatterns = [
    url(r'^s3/$',
        views.S3MockView.as_view(), name='s3mock'),
    url(r'^upload/$',
        FormView.as_view(
            form_class=forms.UploadForm,
            template_name='form.html',
            success_url='/upload/'
        ), name='upload'),
]
