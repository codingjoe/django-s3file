import os

from django.core.files.storage import default_storage


class S3FileMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        file_fields = request.POST.getlist('s3file', [])
        for field_name in file_fields:
            paths = request.POST.getlist(field_name, [])
            request.FILES.setlist(field_name, list(self.get_files_from_storage(paths)))

        return self.get_response(request)

    @staticmethod
    def get_files_from_storage(paths):
        """Return S3 file where the name does not include the path."""
        for path in paths:
            f = default_storage.open(path)
            f.name = os.path.basename(path)
            yield f
