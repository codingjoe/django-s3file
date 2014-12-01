import os
from appconf import AppConf


class S3FileConf(AppConf):
    UPLOAD_PATH = os.path.join('tmp', 's3fine')

    class Meta:
        prefix = "S3FILE"
