from django.core.files import File
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.views import generic

from tests.testapp import forms


class FileEncoder(DjangoJSONEncoder):
    def default(self, o):
        if isinstance(o, File):
            return o.name
        super().default(o)


class ExampleFormView(generic.FormView):
    form_class = forms.UploadForm
    template_name = 'form.html'

    def form_valid(self, form):
        return JsonResponse({
            'POST': self.request.POST,
            'FILES': {
                'file': self.request.FILES.getlist('file'),
                'other_file': self.request.FILES.getlist('other_file'),
            }
        }, status=201, encoder=FileEncoder)
