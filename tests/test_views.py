import base64
import hmac
import http

from s3file import views


class TestS3MockView:
    url = '/__s3_mock__/'

    policy = (
        'eyJDb25kaXRpb25zIjogW3siYnVja2V0IjogInRlc3QtYnVja2V0In0sIFsic3RhcnRz'
        'LXdpdGgiLCAiJGtleSIsICJ0bXAvczNmaWxlLzNlUWhwOTZYU1dldFFwZ1VVQmZzWHci'
        'XSwgeyJzdWNjZXNzX2FjdGlvbl9zdGF0dXMiOiAiMjAxIn0sIFsic3RhcnRzLXdpdGgi'
        'LCAiJENvbnRlbnQtVHlwZSIsICIiXV0sICJFeHBpcmVzSW4iOiAxMjA5NjAwfQ=='
    )
    date = '20190616T184210Z'

    def test_post__bad_request(self, rf):
        request = rf.post(self.url, data={})
        response = views.S3MockView.as_view()(request)
        assert response.status_code == http.HTTPStatus.BAD_REQUEST

    def test_post__created(self, client, upload_file):
        with open(upload_file) as fp:
            response = client.post(self.url, data={
                'x-amz-signature': 'T1Mb71D45h1u2SBoUHOMBNFCI2AgrKAg1UzKdUHUHig=',
                'x-amz-algorithm': 'AWS4-HMAC-SHA256',
                'x-amz-date': self.date,
                'x-amz-credential': 'testaccessid',
                'policy': self.policy,
                'key': 'tmp/s3file/3eQhp96XSWetQpgUUBfsXw/${filename}',
                'success_action_status': '201',
                'file': fp,
            })
        assert response.status_code == http.HTTPStatus.CREATED

    def test_post__bad_signature(self, client, upload_file):

        bad_signature = base64.b64encode(
            hmac.new(b'eve', (self.policy + self.date).encode(), 'sha256').digest()
        ).decode()
        with open(upload_file) as fp:
            response = client.post(self.url, data={
                'x-amz-signature': bad_signature,
                'x-amz-algorithm': 'AWS4-HMAC-SHA256',
                'x-amz-date': self.date,
                'x-amz-credential': 'testaccessid',
                'policy': self.policy,
                'key': 'tmp/s3file/3eQhp96XSWetQpgUUBfsXw/${filename}',
                'success_action_status': '201',
                'file': fp,
            })
        assert response.status_code == http.HTTPStatus.FORBIDDEN

    def test_post__not_a_signature(self, client, upload_file):
        bad_signature = 'eve'
        with open(upload_file) as fp:
            response = client.post(self.url, data={
                'x-amz-signature': bad_signature,
                'x-amz-algorithm': 'AWS4-HMAC-SHA256',
                'x-amz-date': self.date,
                'x-amz-credential': 'testaccessid',
                'policy': self.policy,
                'key': 'tmp/s3file/3eQhp96XSWetQpgUUBfsXw/${filename}',
                'success_action_status': '201',
                'file': fp,
            })
        assert response.status_code == http.HTTPStatus.BAD_REQUEST
