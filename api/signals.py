from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, AccountSettings, JobApplication, JobApplicationReview
from .tasks import send_job_application_submission_email, send_job_application_review_status_email
from django.db import transaction

import logging
# Get an instance of a logger
logger = logging.getLogger(__name__)

CustomUser = get_user_model()

@receiver(post_save, sender=CustomUser)
def notify_profile_settings_created(sender, instance, created, **kwargs):
    # Signal
    if created:
        # Create the profile and Account settings
        user_account_settings = AccountSettings.objects.create()
        user_account_settings.save()
        
        user_profile = Profile.objects.create(user=instance, account_settings=user_account_settings)
        user_profile.save()

        print(f"User account settings and profile created: {user_profile} {user_account_settings}")


@receiver(post_save, sender=JobApplication)
def notify_job_application_submitted(sender, instance, created, **kwargs):
    """
    Create a review and send email only when an application is submitted.
    """
    if instance.job_app_submission_status == "Submitted":
        # Create the application review
        job_app_review, job_app_review_created = JobApplicationReview.objects.get_or_create(
            job_app=instance, reviewed_by=instance.job_post.user)

        # Log the data and send a mail to the user that we have recieved there job application
        if job_app_review_created:
            logger.info(f"Review created for JobApplication {instance.pk}")
            try:
                # Send the email to the user
                email_body = "Hi " + instance.user.get_full_name() +'\nThis is an official email acknowledging receipt of your application.'
                email_body += "\n\nWe will review your application and get back to you soon."
                email_body += "\n\nThank you for your application."
                data = {
                    "email_subject":"Application recieved",
                    "email_body":email_body, 
                    "to_email":instance.user.email
                    }
        
                transaction.on_commit(lambda: send_job_application_submission_email.delay(data))
                logger.info("Job application review created and email queued.")
            except Exception as e:
                logger.info({"message": "Job application review email task could not be queued. Please try again later.","error": str(e)})
        else:
            logger.info(f"Review already exists for JobApplication {instance.pk}")


@receiver(post_save, sender=JobApplicationReview)
def notify_job_application_reviewed(sender, instance, created, **kwargs):
    if instance.job_applicatiion_review == "Reviewed":
        # Send an email to the user that their application has been reviewed and the status
        logger.info(f"Job application Reviewed for {instance.job_app}")
        try:
            email_body ="Hi " + instance.job_app.user.get_full_name()+ "\n\n"
            email_body   += "\n\n" + instance.reason + "\\nnThank you for your application"
            data = {
                "email_subject":"Your Job Application Review Outcome",
                "email_body":email_body, 
                "to_email":instance.job_app.user.email
                }
            transaction.on_commit(lambda: send_job_application_review_status_email.delay(data))
            logger.info("Job application review status sent to user queued")

        except Exception as e:
                logger.info({"message": "Job application review task could not be queued. Please try again later.","error": str(e)})





