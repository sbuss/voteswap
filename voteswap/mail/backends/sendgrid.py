from __future__ import absolute_import
from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend
from django.core.mail.message import sanitize_address
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Content
from sendgrid.helpers.mail import Mail
from sendgrid.helpers.mail import Email
from sendgrid.helpers.mail import Personalization


class SendGridBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        client = SendGridAPIClient(apikey=settings.SENDGRID_API_KEY)
        for message in email_messages:
            mail = Mail()
            mail.set_from(Email(sanitize_address(
                message.from_email, message.encoding)))
            mail.set_subject(message.subject)
            personalization = Personalization()
            for recipient in message.recipients():
                personalization.add_to(Email(sanitize_address(
                    recipient, message.encoding)))
            mail.add_personalization(personalization)
            if message.reply_to:
                mail.set_reply_to(Email(sanitize_address(
                    message.reply_to[0], message.encoding)))
            mail.add_content(Content("text/plain", message.body))
            for content, mimetype in message.alternatives:
                mail.add_content(Content(mimetype, content))
            client.client.mail.send.post(request_body=mail.get())
