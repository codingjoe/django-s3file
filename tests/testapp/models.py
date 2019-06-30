from django.db import models


class FileModel(models.Model):
    file = models.FileField(upload_to='path/to/files', blank=True)
    other_file = models.FileField(upload_to='path/to/files', blank=True)
