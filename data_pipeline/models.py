from django.db import models
import uuid
from django.conf import settings

class ETLRun(models.Model):
    TRIGGER_TYPES = [
        ("Scheduled", "Scheduled"),
        ("Manual", "Manual"),
    ]
    ETL_STATUS = [
        ("Running", "Running"),
        ("Completed", "Completed"),
        ("Failed", "Failed"),
    ]

    run_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    system_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='etl_runs')
    trigger_type = models.CharField(max_length=20, choices=TRIGGER_TYPES, default="Manual")
    elt_status = models.CharField(max_length=20, choices=ETL_STATUS, default="Running")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    duration_seconds = models.FloatField(blank=True, null=True)
    pages_fetched = models.IntegerField(default=0)
    jobs_extracted_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"ETL RUN {self.run_id} - {self.trigger_type} - {self.elt_status}"
