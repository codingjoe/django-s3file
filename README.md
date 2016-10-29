# django-s3file


A lightweight file upload input for Django and Amazon S3.

[![PyPi Version](https://img.shields.io/pypi/v/django-s3file.svg)](https://pypi.python.org/pypi/django-s3file/)
[![Build Status](https://travis-ci.org/codingjoe/django-s3file.svg?branch=master)](https://travis-ci.org/codingjoe/django-s3file)
[![Code Health](https://landscape.io/github/codingjoe/django-s3file/master/landscape.svg?style=flat)](https://landscape.io/github/codingjoe/django-s3file/master)
[![Test Coverage](https://coveralls.io/repos/codingjoe/django-s3file/badge.svg?branch=master)](https://coveralls.io/r/codingjoe/django-s3file)
[![Code health](https://scrutinizer-ci.com/g/codingjoe/django-s3file/badges/quality-score.svg?b=master)](https://scrutinizer-ci.com/g/codingjoe/django-s3file/?branch=master)
[![GitHub license](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/codingjoe/django-s3file/master/LICENSE)
[![Join the chat at https://gitter.im/codingjoe/django-s3file](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/codingjoe/django-s3file?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)


## Features

 - Pure JavaScript (no jQuery)
 - Python 2 and 3 support
 - Auto swapping based on your environment
 - Pluggable as it returns a simple django file, just like native input
 - Easily extensible (authentication, styles)


## Installation

Just install S3file using `pip` or `easy_install`.
```bash
pip install django-s3file
```
Don't forget to add `s3file` to the `INSTALLED_APPS`.


## Usage

### Simple integrations

Include s3file's URLs in your URL root.

**urls.py**
```python
urlpatterns = patterns(
    ...
    url(r'^s3file/', include('s3file.urls')),
)
```

**forms.py**
```python
from s3file.forms import AutoFileInput

class MyModelForm(forms.ModelForm):

    class Meta:
        model = MyModel
        fields = ('my_file_field')
        widgets = {
            'my_file_field': AutoFileInput
        }
```
**Done!** No really, that's all that needs to be done.


### Setting up the CORS policy on your AWS S3 Bucket

```xml
<CORSConfiguration>
    <CORSRule>
        <AllowedOrigin>*</AllowedOrigin>
        <AllowedMethod>PUT</AllowedMethod>
        <AllowedMethod>POST</AllowedMethod>
        <AllowedMethod>GET</AllowedMethod>
        <MaxAgeSeconds>3000</MaxAgeSeconds>
        <AllowedHeader>*</AllowedHeader>
    </CORSRule>
</CORSConfiguration>
```


### Advanced usage examples

#### Authentication
The signing endpoint supports CSRF by default but does not require a authenticated user.
This and other behavior can be easily added by inheriting from the view.

**views.py**
```python
from s3file.views import S3FileView
from braces.views import LoginRequiredMixin

class MyS3FileView(LoginRequiredMixin, S3FileView):
    pass
```

Now don't forget to change the URLs.

**urls.py**
```python
urlpatterns = patterns(
    ...
    url('^s3file/sign',
        MyS3FileView.as_view(), name='s3file-sign'),
)
```

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
