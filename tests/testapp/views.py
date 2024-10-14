from django.core.files import File
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views import generic

from . import forms, models


class FileEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, File):
            return o.name
        return super().default(o)


class ExampleCreateView(generic.CreateView):
    model = models.FileModel
    fields = ["file", "other_file"]
    template_name = "form.html"

    def form_valid(self, form):
        return JsonResponse(
            {
                "POST": self.request.POST,
                "FILES": {
                    "file": self.request.FILES.getlist("file"),
                    "other_file": self.request.FILES.getlist("other_file"),
                },
                "QUERY_STRING": self.request.GET,
            },
            status=201,
            encoder=FileEncoder,
        )


class ExampleUpdateView(generic.UpdateView):
    model = models.FileModel
    form_class = forms.FileForm
    template_name = "form.html"

    def form_valid(self, form):
        return JsonResponse(
            {
                "POST": self.request.POST,
                "FILES": {
                    "file": self.request.FILES.getlist("file"),
                    "other_file": self.request.FILES.getlist("other_file"),
                },
                "QUERY_STRING": self.request.GET,
            },
            status=201,
            encoder=FileEncoder,
        )


class MultiExampleFormView(generic.FormView):
    form_class = forms.MultiUploadForm
    template_name = "form.html"

    def form_valid(self, form):
        return JsonResponse(
            {
                "POST": self.request.POST,
                "FILES": {
                    "file": self.request.FILES.getlist("file"),
                    "other_file": self.request.FILES.getlist("other_file"),
                },
            },
            status=201,
            encoder=FileEncoder,
        )
