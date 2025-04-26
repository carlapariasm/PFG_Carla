# sendgrid_backend.py
from django.core.mail.backends.base import BaseEmailBackend  
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email

class SendGridEmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent_count = 0
        sg = SendGridAPIClient('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')  # Reemplaza por tu API key
        for message in email_messages:
            content = message.body
            mail = Mail(
                from_email=message.from_email,
                to_emails=message.to,  # Aquí es donde se pasa la lista de correos
                subject=message.subject,
                plain_text_content=content,
            )
            try:
                response = sg.send(mail)
                if 200 <= response.status_code < 300:
                    sent_count += 1
            except Exception as e:
                if not self.fail_silently:
                    raise
        return sent_count
