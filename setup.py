#!/usr/bin/env python
from setuptools import setup

setup(
    name='django-s3file',
    version='3.0.0',
    description='A lightweight file uploader input for Django and Amazon S3',
    author='codingjoe',
    url='https://github.com/codingjoe/django-s3file',
    author_email='info@johanneshoppe.com',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
        "Programming Language :: Python :: 3",
    ],
    packages=['s3file'],
    include_package_data=True,
    install_requires=[
        'django-storages',
        'boto3',
    ],
)
