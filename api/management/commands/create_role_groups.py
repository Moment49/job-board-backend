from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
import logging 

CustomUser = get_user_model()

#Set the logger entry point
logger = logging.getLogger('api.views')


class Command(BaseCommand):
    help= "Automatically create only role Groups for (SYSTEM, ADMIN & USER). Note this script must be run once"

    def handle(self, *args, **options):
        # Create the groups
        Admin_group, created = Group.objects.get_or_create(name="Admin")
        User_group, created = Group.objects.get_or_create(name="User")
        System_group, created = Group.objects.get_or_create(name='System')

        if not created:
            logger.error(f"An errror occurred while creating the Role Groups")
            raise CommandError(f"An errror occurred while creating the Role Groups")

        logger.info(f'The Role Groups: {System_group}, {Admin_group} and {User_group} created sucessfully')
        self.stdout.write(
            self.style.SUCCESS(f'The Role Groups: {System_group}, {Admin_group} and {User_group} created sucessfully')
        )
    
           

