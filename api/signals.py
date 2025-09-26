from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from .models import Profile, AccountSettings
import logging
# Get an instance of a logger
# logger = logging.getLogger(__name__)

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


