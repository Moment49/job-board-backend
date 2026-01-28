from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.conf import settings
from django.contrib.auth.models import Group
import logging

CustomUser = get_user_model()


#Set the logger entry point
logger = logging.getLogger('api.views')


class Command(BaseCommand):
    help = "Creates a system user with SYSTEM role. Note: This script must be run once"

    def add_arguments(self, parser):
        parser.add_argument("-system_email", '--system_user_email', type=str, help="System user email to be used \
        to verify the email in env")


    def handle(self, *args, **options):
        # Check that the user email entered matches what is in thhe env settings 
        # Note: The system email in the env file will be secured via a secrets module (Implement later)
        system_user_email = options['system_user_email']

        # Get the System user Group
        system_group, created = Group.objects.get_or_create(name='System')

        if system_user_email != settings.SYSTEM_USER_EMAIL:
            logger.error(f"Error - Invalid system user email {system_user_email}")
            raise CommandError(f"Error - Invalid system user email {system_user_email}")
        else:  
            try:
                system_user = CustomUser.objects.get(email=settings.SYSTEM_USER_EMAIL)

                # Check to ensure that only one system user exists with email and in the System group
                if system_user.groups.filter(name='System').exists():
                    logger.error(f"A system user with email {settings.SYSTEM_USER_EMAIL} already exists")
                    raise CommandError(f"A system user with email {settings.SYSTEM_USER_EMAIL} already exists.")          
                else:
                    # Assign user to System Group
                    system_user.groups.add(system_group)

            except CustomUser.DoesNotExist:
                system_user = CustomUser.objects.create_superuser(
                    email=settings.SYSTEM_USER_EMAIL,
                    first_name="System",
                    last_name="Service",
                    password="Default password"
                )
                system_user.is_active = True
                system_user.is_staff = False
                system_user.is_superuser = False
                system_user.set_unusable_password()  # System user should not be able to log in
                system_user.role = "SYSTEM"
                system_user.save()

                # Assign the user to the System Group
                system_user.groups.add(system_group)

                logger.info(f'System user with email {settings.SYSTEM_USER_EMAIL} created successfully')
                self.stdout.write(
                    self.style.SUCCESS(f'System user with email {settings.SYSTEM_USER_EMAIL} created successfully')
                )
          