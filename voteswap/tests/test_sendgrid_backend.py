from django.core.mail import EmailMultiAlternatives
from django.test import override_settings
from django.test import TestCase
from mock import patch
from mock import MagicMock


@override_settings(
    EMAIL_BACKEND='voteswap.mail.backends.sendgrid.SendGridBackend')
class TestEmailBase(TestCase):
    def setUp(self):
        self.patched_client_instance = MagicMock()
        self.patcher = patch(
            'voteswap.mail.backends.sendgrid.SendGridAPIClient',
            return_value=self.patched_client_instance)
        self.patched_client = self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def _get_email(self):
        message = EmailMultiAlternatives(
            from_email=u'noreply@email.voteswap.us',
            to=['to@example.com'],
            reply_to=['replyto@example.com'],
            subject=u"Test email",
            body='Test body')
        message.attach_alternative('<html>html body</html>', 'text/html')
        return message

    def test_called(self):
        from voteswap.mail.backends.sendgrid import SendGridBackend
        with patch.object(SendGridBackend, 'send_messages') as mock_sendgrid:
            message = self._get_email()
            message.send()
            mock_sendgrid.assert_called_with([message])

    def test_apikey(self):
        with override_settings(SENDGRID_API_KEY='foobar'):
            message = self._get_email()
            message.send()
            self.patched_client.assert_called_with(apikey='foobar')

    def test_send(self):
        message = self._get_email()
        message.send()
        send_mail_request = (
            self.patched_client_instance.client.mail.send.post.call_args[1])
        content = send_mail_request['request_body']
        self.assertEqual(content['from']['email'], message.from_email)
        self.assertEqual(content['personalizations'][0]['to'][0]['email'],
                         message.recipients()[0])
        self.assertEqual(len(content['content']), 2)
        for body in content['content']:
            if body['type'] == 'text/plain':
                self.assertEqual(body['value'], message.body)
            else:
                self.assertEqual(body['value'], message.alternatives[0][0])
