# Write tasks here
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
import logging
import smtplib 

logger = logging.getLogger(__name__)

@shared_task
def send_verification_email(data):
    try:
        # Send activation email
        msg = EmailMessage(
        subject=data['email_subject'],
        body=data['email_body'],
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[data['to_email']],
        )
        msg.send(fail_silently=False)
        logger.info(f"✅ Email queued for {data['to_email']}")
        return {"status": "sent"}

    except smtplib.SMTPAuthenticationError:
        logger.error("❌ SMTP authentication failed. Check SendGrid API key.")
    except smtplib.SMTPConnectError:
        logger.error("❌ Could not connect to the SMTP server. Check your internet connection or email service configuration.")


@shared_task
def send_job_application_submission_email(data):
    try:
        msg = EmailMessage(
            subject=data["email_subject"],
            body=data['email_body'],
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[data['to_email']]
        )
        msg.send(fail_silently=False)
        logger.info(f"✅ Email queued for {data['to_email']}")
        return {"status": "sent"}
    except smtplib.SMTPAuthenticationError:
        logger.error("❌ SMTP authentication failed. Check SendGrid API key.")
    except smtplib.SMTPConnectError:
        logger.error("❌ Could not connect to the SMTP server. Check your internet connection or email service configuration.")


@shared_task
def send_job_application_review_status_email(data):
    try:
        msg = EmailMessage(
            subject=data["email_subject"],
            body=data['email_body'],
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[data['to_email']]
        )
        msg.send(fail_silently=False)
        logger.info(f"✅ Email queued for {data['to_email']}")
        return {"status": "sent"}
    except smtplib.SMTPAuthenticationError:
        logger.error("❌ SMTP authentication failed. Check SendGrid API key.")
    except smtplib.SMTPConnectError:
        logger.error("❌ Could not connect to the SMTP server. Check your internet connection or email service configuration.")

       
             