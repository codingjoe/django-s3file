import base64
import hashlib
import hmac
import logging

from django import http
from django.conf import settings
from django.core.files.storage import default_storage
from django.views import generic

logger = logging.getLogger('s3file')


class S3MockView(generic.View):

    def post(self, request):
        success_action_status = request.POST.get('success_action_status', 201)
        try:
            file = request.FILES['file']
            key = request.POST['key']
            date = request.POST['x-amz-date']
            signature = request.POST['x-amz-signature']
            policy = request.POST['policy']
        except KeyError:
            logger.exception('bad request')
            return http.HttpResponseBadRequest()

        try:
            signature = base64.b64decode(signature.encode())
            policy = base64.b64decode(policy.encode())

            calc_sign = hmac.new(
                settings.SECRET_KEY.encode(),
                policy + date.encode(),
                'sha256'
            ).digest()
        except ValueError:
            logger.exception('bad request')
            return http.HttpResponseBadRequest()

        if not hmac.compare_digest(signature, calc_sign):
            logger.warning('bad signature')
            return http.HttpResponseForbidden()

        key = key.replace('${filename}', file.name)
        etag = hashlib.md5(file.read()).hexdigest()  # nosec
        file.seek(0)
        key = default_storage.save(key, file)
        return http.HttpResponse(
            "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
            "<PostResponse>"
            f"<Location>{settings.MEDIA_URL}{key}</Location>"
            f"<Bucket>{getattr(settings, 'AWS_STORAGE_BUCKET_NAME')}</Bucket>"
            f"<Key>{key}</Key>"
            f"<ETag>\"{etag}\"</ETag>"
            "</PostResponse>",
            status=success_action_status,
        )
