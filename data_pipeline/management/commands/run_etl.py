from django.core.management.base import BaseCommand, CommandError
from data_pipeline.utils.etl_process import call_external_api
import logging


logger = logging.getLogger('data_pipeline.utils.etl_process')


class Command(BaseCommand):
    help = "Run the ETL process to fetch job data from external API"

    def handle(self, *args, **options):
        try:
            # call_external_api()
            print("Starting ETL process...")
            call_external_api_gen = call_external_api()
            print(call_external_api_gen)
            for data in call_external_api_gen:
                logger.info(f"Fetched data: {data}")
                print(data)
            print("ETL process completed successfully.")
            self.stdout.write(self.style.SUCCESS("Successfully ran the ETL process (--dry run)"))

        except Exception as e:
            raise CommandError(f"Error running ETL process: {e}")