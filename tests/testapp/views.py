from django.core.files.storage import default_storage
from django.http import response
from django.views import generic


class S3MockView(generic.View):

    def post(self, request):
        key = request.POST.get('key')
        file = request.FILES.get('file', None)
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
