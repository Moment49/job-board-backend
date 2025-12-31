from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model

CustomUser = get_user_model()


class Command(BaseCommand):
    help= ""

    def handle(self, *args, **options):
        # Create the groups
        ...