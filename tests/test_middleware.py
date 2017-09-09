from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.files.uploadedfile import SimpleUploadedFile

from s3file.middleware import S3FileMiddleware


class TestS3FileMiddleware:

    def test_get_files_from_storage(self):
        content = b'test_get_files_from_storage'
        default_storage.save('test_get_files_from_storage', ContentFile(content))
        files = S3FileMiddleware.get_files_from_storage(['test_get_files_from_storage'])
        file = next(files)
        assert file.read() == content

    def test_process_request(self, rf):
        uploaded_file = SimpleUploadedFile('uploaded_file.txt', b'uploaded')
        request = rf.post('/', data={'file': uploaded_file})
        S3FileMiddleware().process_request(request)
        assert request.FILES.getlist('file')
        assert request.FILES.get('file').read() == b'uploaded'

        default_storage.save('s3_file.txt', ContentFile(b's3file'))
        request = rf.post('/', data={'file': 's3_file.txt', 's3file': 'file'})
        S3FileMiddleware().process_request(request)
        assert request.FILES.getlist('file')
        assert request.FILES.get('file').read() == b's3file'
