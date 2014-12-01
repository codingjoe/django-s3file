#!/usr/bin/env python
from setuptools import setup, Command


class PyTest(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import sys
        import subprocess

        errno = subprocess.call([sys.executable, 'runtests.py'])
        raise SystemExit(errno)


setup(
    name='django-s3file',
    version='0.4.1',
    description='A lightweight Fine Uploader input for Django and Amazon S3',
    author='codingjoe',
    url='https://github.com/codingjoe/django-s3file',
    author_email='info@johanneshoppe.com',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Framework :: Django',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
    packages=['s3file'],
    include_package_data=True,
    install_requires=[
        'django-appconf==0.6',
    ],
    cmdclass={'test': PyTest},
)
