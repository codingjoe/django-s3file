# django-s3file

A lightweight file upload input for Django and Amazon S3.

Django-S3File allows you to upload files directly AWS S3 effectively
bypassing your application server. This allows you to avoid long running
requests from large file uploads.

[![PyPi Version](https://img.shields.io/pypi/v/django-s3file.svg)](https://pypi.python.org/pypi/django-s3file/)
[![Build Status](https://travis-ci.org/codingjoe/django-s3file.svg?branch=master)](https://travis-ci.org/codingjoe/django-s3file)
[![Test Coverage](https://coveralls.io/repos/codingjoe/django-s3file/badge.svg?branch=master)](https://coveralls.io/r/codingjoe/django-s3file)
[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/codingjoe/django-s3file/master/LICENSE)

## Features

*   lightweight: less 200 lines
*   no JavaScript or Python dependencies (no jQuery)
*   easy integration
*   works just like the build-in

## Installation

_Make sure you have [Amazon S3 storage][boto-storage] setup correctly._

Just install S3file using `pip`.

```bash
pip install django-s3file
```

Add the S3File app and middleware in your settings:

```python

INSTALLED_APPS = (
    '...',
    's3file',
    '...',
)

MIDDLEWARE = (
    '...',
    's3file.middleware.S3FileMiddleware',
    '...',
)
```

[boto-storage]: http://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html

## Usage

S3File automatically replaces Django's `ClearableFileInput` widget,
you do not need to alter your code at all.

The `ClearableFileInput` widget is only than automatically replaced when the
`DEFAULT_FILE_STORAGE` setting is set to `django-storages`' `S3Boto3Storage`.

### Setting up the AWS S3 bucket

### Upload folder

S3File uploads to a single folder. Files are later moved by Django when
they are saved to the `upload_to` location.

It is recommended to [setup expiration][aws-s3-lifecycle-rules] for that folder, to ensure that
old and unused file uploads don't add up and produce costs.

[aws-s3-lifecycle-rules]: http://docs.aws.amazon.com/AmazonS3/latest/dev/intro-lifecycle-rules.html

The default folder name is: `tmp/s3file`
You can change it by changing the `S3FILE_UPLOAD_PATH` setting.

### CORS policy

You will need to allow `POST` from all origins.
Just add the following to your CORS policy. 

```xml
<CORSConfiguration>
    <CORSRule>
        <AllowedOrigin>*</AllowedOrigin>
        <AllowedMethod>POST</AllowedMethod>
        <AllowedMethod>GET</AllowedMethod>
        <MaxAgeSeconds>3000</MaxAgeSeconds>
        <AllowedHeader>*</AllowedHeader>
    </CORSRule>
</CORSConfiguration>
```

### Uploading multiple files

Django does have limited [support to uploaded multiple files][uploading-multiple-files].
S3File fully supports this feature. The custom middleware makes ensure that files
are accessible via `request.FILES`, even thogh they have been uploaded to AWS S3 directly
and not to your Django application server.

[uploading-multiple-files]: https://docs.djangoproject.com/en/1.11/topics/http/file-uploads/#uploading-multiple-files

### Security and Authentication

django-s3file does not require any authentication setup. Files can only be uploaded
to AWS S3 by users who have access to the form where the file upload is requested.

You can further limit user data using the [`accept`][att_input_accept]-attribute.
The specified MIME-Type will be enforced in the AWS S3 policy as well, for enhanced
server side protection.

S3File uses a strict policy and signature to grant clients permission to upload
files to AWS S3. This signature expires based on Django's
[`SESSION_COOKIE_AGE`][setting-SESSION_COOKIE_AGE] setting.

[setting-SESSION_COOKIE_AGE]: https://docs.djangoproject.com/en/1.11/ref/settings/#std:setting-SESSION_COOKIE_AGE
[att_input_accept]: https://www.w3schools.com/tags/att_input_accept.asp

## License

The MIT License (MIT)

Copyright (c) 2014 Johannes Hoppe

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
