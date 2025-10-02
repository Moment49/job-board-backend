from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, AccountSettings, JobApplication, JobApplicationReview
from .tasks import send_job_submition_mail
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
def notify_job_application_created(sender, instance, created, **kwargs):
    if created or instance.job_app_submission_status == "Submitted":
        # Create the application review
        job_app_review = JobApplicationReview.objects.create(job_app=instance, reviewed_by=instance.job_post.user)

        # Log the data and send a mail to the user that we have recieved there job application
        job_app_review.save()
        try:
            # Send the email to the user
            email_body = "Hi " + instance.user.get_full_name() +'\nThis is a official email acknowlegeing the recipent of your application'
            data = {"email_subject":"Application recieved",
            "email_body":email_body, "to_email":instance.user.email}
            
            transaction.on_commit(lambda: send_job_submition_mail.delay(data))
        except Exception as e:
            logger.info({"message": "Verification task could not be queued. Please try again later.","error": str(e)})

        logger.info({"message": "Job application review created successfully."})




