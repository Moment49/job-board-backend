from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

CustomUser = get_user_model()

class Command(BaseCommand):
    help= "Automatically create only role Groups for (ADMIN & USER). Note this script must be run once"

    def handle(self, *args, **options):
        # Create the groups
        Admin_group, created = Group.objects.get_or_create(name="Admin")
        User_group, created = Group.objects.get_or_create(name="User")

        if not created:
            raise CommandError(f"An errror occurred while creating the Role Groups")

        self.stdout.write(
            self.style.SUCCESS(f'The Role Groups: {Admin_group} and {User_group} created sucessfully')
        )
    
           

