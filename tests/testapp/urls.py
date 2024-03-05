try:
    from django.urls import include, path
except ImportError:
    from django.conf.urls import url as path

from . import views

urlpatterns = [
    path(
        "example/",
        include(
            [
                path(
                    "create", views.ExampleCreateView.as_view(), name="example-create"
                ),
                path(
                    "<int:pk>/update",
                    views.ExampleUpdateView.as_view(),
                    name="example-update",
                ),
            ]
        ),
    ),
    path("multi/", views.MultiExampleFormView.as_view(), name="upload-multi"),
]
