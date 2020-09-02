try:
    from django.urls import path
except ImportError:
    from django.conf.urls import url as path

from . import views

urlpatterns = [
    path("", views.ExampleFormView.as_view(), name="upload"),
]
