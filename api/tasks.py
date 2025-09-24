# Write tasks here
from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_email_verify(data):
    send_mail(
    'Subject here',
    'Here is the message.',
    'from@example.com',
    ['to@example.com'],
    fail_silently=False,
    )