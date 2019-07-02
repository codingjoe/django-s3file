from django.urls import path

from . import views

urlpatterns = [
    path('', views.ExampleFormView.as_view(), name='upload'),
    path('', views.UploadFormDirectoryView.as_view(), name='upload_directory'),
]
