# Security Policy

## Security Considerations

The wake of CVE-2022-24840 revealed the importance to document security considerations.
The following attack vectors have been considered during development. Should there be
a possible vector or consideration missing, please contact the maintainers, as described
below.

We use [pre-signed POST URLs](s3-pre-signed-url) to upload files to AWS S3.
[Django's internal signer](django-signing) is used to sign the upload path and validate
it before fetching files from S3.

Please note, that Django's signer uses the `SECRET_KEY`, rotating the key will void all
signatures. Should you rotate the secret key, between a form GET and POST request, the
form will fail. Similarly, Django will expire all sessions if you rotate the key.

[s3-pre-signed-url]: https://boto3.amazonaws.com/v1/documentation/api/latest/guide/s3-presigned-urls.html
[django-signing]: https://docs.djangoproject.com/en/stable/topics/signing/

### Upload of malicious files

AWS S3 supports MIME type detection and content-type enforcement.
You can limit the upload of malicious files via the MIME type [accept][accept].
However, this is not a security measure, and you should always validate files before
processing them.

[accept]: https://developer.mozilla.org/en-US/docs/Web/HTML/Attributes/accept

### Request file injection

Though files can always be included in a request, CVE-2022-24840 revealed that we need
to consider people injecting any files that reside on your S3 bucket. However, we do
presign the upload location and validate it before fetching files from S3.

### Path traversal & timing attacks

We fetch files from your S3 bucket. This behavior could be used to brute force valid
file names. We mitigate this by signing the allowed upload path and validating it.
The upload path is unique for each file input and request. Therefore, an attacker can
not escape and access any files but the one uploaded by the attacker.

## Reporting a Vulnerability

NEVER open an issue or discussion to report a vulnerability. Please contact one of the
maintainers of the project either via email or Telegram:

* Email: [johannes@maron.family](mailto:johannes@maron.family)
* Telegram: [@codingjoe](https://t.me/codingjoe)
