from django.core.management.base import BaseCommand, CommandError
from data_pipeline.utils.etl_process import extract_jobs_from_arbeitnow, transform_load_jobs
import logging


logger = logging.getLogger('data_pipeline.utils.etl_process')


class Command(BaseCommand):
    help = "Run the ETL process to fetch job data from external API"

    def handle(self, *args, **options):
        try:
            print("Starting ETL process...")
            
            extract_jobs = extract_jobs_from_arbeitnow()
            for data in extract_jobs:
                transform_data = transform_load_jobs(data)
                logger.info(f"Transformed data: {transform_data}")
            

            print("ETL process completed successfully.")
            self.stdout.write(self.style.SUCCESS("Successfully ran the ETL process (--dry run)"))

        except Exception as e:
            raise CommandError(f"Error running ETL process: {e}")