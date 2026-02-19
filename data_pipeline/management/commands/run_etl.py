from django.core.management.base import BaseCommand, CommandError
from data_pipeline.utils.etl_process import call_external_api


class Command(BaseCommand):
    help = "Run the ETL process to fetch job data from external API"

    def handle(self, *args, **options):
        try:
            call_external_api()
            self.stdout.write(self.style.SUCCESS("Successfully ran the ETL process (--dry run)"))
        except Exception as e:
            raise CommandError(f"Error running ETL process: {e}")