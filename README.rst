django-s3file
=============

A lightweight file upload input for Django and Amazon S3.

Django-S3File allows you to upload files directly AWS S3 effectively
bypassing your application server. This allows you to avoid long running
requests from large file uploads. This is particuallary helpful for if
you run your service on AWS Lambda or Heroku where you have a hard request
limit.

|PyPi Version| |Build Status| |Test Coverage| |GitHub license|

Features
--------

-  lightweight: less 200 lines
-  no JavaScript or Python dependencies (no jQuery)
-  easy integration
-  works just like the built-in

For the Nerds
-------------

.. image:: http-message-flow.svg

Installation
------------

Make sure you have `Amazon S3 storage`_ setup correctly.

Just install S3file using ``pip``.

.. code:: bash

    pip install django-s3file

Add the S3File app and middleware in your settings:

.. code:: python


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

Usage
-----

S3File automatically replaces Django’s ``ClearableFileInput`` widget,
you do not need to alter your code at all.

The ``ClearableFileInput`` widget is only than automatically replaced
when the ``DEFAULT_FILE_STORAGE`` setting is set to
``django-storages``\ ’ ``S3Boto3Storage``.

Setting up the AWS S3 bucket
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Upload folder
~~~~~~~~~~~~~

S3File uploads to a single folder. Files are later moved by Django when
they are saved to the ``upload_to`` location.

It is recommended to `setup expiration`_ for that folder, to ensure that
old and unused file uploads don’t add up and produce costs.

The default folder name is: ``tmp/s3file`` You can change it by changing
the ``S3FILE_UPLOAD_PATH`` setting.

CORS policy
~~~~~~~~~~~

You will need to allow ``POST`` from all origins. Just add the following
to your CORS policy.

.. code:: xml

    <CORSConfiguration>
        <CORSRule>
            <AllowedOrigin>*</AllowedOrigin>
            <AllowedMethod>POST</AllowedMethod>
            <AllowedMethod>GET</AllowedMethod>
            <MaxAgeSeconds>3000</MaxAgeSeconds>
            <AllowedHeader>*</AllowedHeader>
        </CORSRule>
    </CORSConfiguration>

Uploading multiple files
~~~~~~~~~~~~~~~~~~~~~~~~

Django does have limited support for `uploading multiple files`_. S3File
fully supports this feature. The custom middleware makes ensure that
files are accessible via ``request.FILES``, even though they have been
uploaded to AWS S3 directly and not to your Django application server.

.. _Amazon S3 storage: http://django-storages.readthedocs.io/en/latest/backends/amazon-S3.html
.. _setup expiration: http://docs.aws.amazon.com/AmazonS3/latest/dev/intro-lifecycle-rules.html
.. _uploading multiple files: https://docs.djangoproject.com/en/stable/topics/http/file-uploads/#uploading-multiple-files

.. |PyPi Version| image:: https://img.shields.io/pypi/v/django-s3file.svg
   :target: https://pypi.python.org/pypi/django-s3file/
.. |Build Status| image:: https://travis-ci.org/codingjoe/django-s3file.svg?branch=master
   :target: https://travis-ci.org/codingjoe/django-s3file
.. |Test Coverage| image:: https://codecov.io/gh/codingjoe/django-s3file/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/codingjoe/django-s3file
.. |GitHub license| image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: https://raw.githubusercontent.com/codingjoe/django-s3file/master/LICENSE
