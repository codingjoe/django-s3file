from django.core.files.storage import default_storage
from django.http import JsonResponse, response
from django.views import generic

from tests.testapp import forms


class S3MockView(generic.View):

    def post(self, request):
        file = request.FILES.get('file', None)
        key = request.POST.get('key')
        key = key.replace('${filename}', file.name)
        default_storage.save(key, file)
        return response.HttpResponse(
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<PostResponse>'
            '<Location></Location>'
            '<Bucket>AWS_STORAGE_BUCKET_NAME</Bucket>'
            '<Key>%s</Key>'
            '<ETag>"1e2580c388265551922a1f73ae5954a3"</ETag>'
            '</PostResponse>' % key,
            status=201)


class ExampleFormView(generic.FormView):
    form_class = forms.UploadForm
    template_name = 'form.html'

    def form_valid(self, form):
        return JsonResponse(self.request.POST, status=201)
