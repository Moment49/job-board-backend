# Write tasks here
from celery import shared_task
from django.core.mail import EmailMessage
from django.conf import settings
import logging
import smtplib 
import requests
import functools
import time
from django.core.cache import cache
from .models import RequestLog



logger = logging.getLogger('api.tasks')

SMTP_AUTH_FAILED_MS ="❌ SMTP authentication failed. Check SendGrid API key."
SMTP_CONN_FAILED_MSG ="❌ Could not connect to the SMTP server. Check your internet connection or email service configuration"

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
        logger.error(f"{SMTP_AUTH_FAILED_MSG}")
    except smtplib.SMTPConnectError:
        logger.error(f"{SMTP_CONN_FAILED_MSG}")



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
        logger.error(f"{SMTP_AUTH_FAILED_MSG}")
    except smtplib.SMTPConnectError:
        logger.error(f"{SMTP_CONN_FAILED_MSG}")


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
         logger.error(f"{SMTP_AUTH_FAILED_MSG}")
    except smtplib.SMTPConnectError:
        logger.error(f"{SMTP_CONN_FAILED_MSG}")


def retry_on_failure(max_retries, countdown):
    def decorator_retry_on_failure(func):

        @functools.wraps(func)
        def wrapper_retry_on_failure(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except requests.exceptions.RequestException as e:
                retries = self.request.retries
                if max_retries >= retries:
                    logger.error(f"Task {self.name} failed after {max_retries} retries")
                    raise e
                
                logger.warning(f"Retrying {self.name} ({retries + 1}/{max_retries}) "
                    f"in {countdown}s due to: {exc}")

                self.retry(countdown=countdown * (2 ** retries), exc=e)
                   

        return wrapper_retry_on_failure
    return decorator_retry_on_failure



@shared_task(bind=True, max_retries=3)
@retry_on_failure(max_retries=3, countdown=3)
def fetch_ip_data(self, ip_address, path, timestamp):
    # Call the primary geolocation API (ipapi) 
    API_KEY = settings.IP_GEOLOCATION_SETTINGS.get('BACKEND_API_KEY')
    url = f"http://api.ipapi.com/{ip_address}?access_key={API_KEY}"
    res = requests.get(url, timeout=10)

    data = None # Initialize variable to store API response

    # Handle successful response from ipapi ---
    if res.status_code == 200:
        data = res.json()

    # Handle rate limits (HTTP 429)     
    elif res.status_code == 429:
        logger.warning(f"429 Too Many Requests for IP {ip_address}")

        # Fallback to secondary API (ipwho.is)
        url = f" https://ipwho.is/{ip_address}"
        try:
            res = requests.get(url, timeout=5)
            data = res.json()
        except Exception as e:
            logger.error(f"Fallback to ipwho.is failed for {ip_address}: {e}")
            return None
        
    # Safely extract fields (supporting both APIs)    
    ip_address = data['ip']
    country = data['country']
    city = data['city']

    # Build unique cache key per IP
    cache_key =  f"ip_addr_{ip_address}"

    # Save the geolocation data to the database
    request_log = RequestLog.objects.create(
        ip_address=ip_address,
        country=country,
        city=city,
        path=path,
        timestamp=timestamp
    )
    # Save the new log entry
    request_log.save()

    # Prepare data for caching
    request_log = {
        'ip_address': ip_address,
        'country': country,
        'city': city,
        'path': path,
        'timestamp': str(timestamp)
    }
    # Cache the data for 1 hour
    cache.set(cache_key, request_log, timeout=3600)

    # Log successful creation 
    logger.info(f"New log created - IP: {ip_address}, Country: {country},\
                    City: {city}, Path: {path}, Timestamp: {timestamp}")


