import uuid

from django.db import models


class Configuration(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dateofcreation = models.DateField(auto_now_add=True, null=True)
    bursary_start_at = models.IntegerField(default=0.00)
    grant_start_at = models.IntegerField(default=0.00)
    receipt_start_at = models.IntegerField(default=0.00)
    voucher_start_at = models.IntegerField(default=0.00)
    school = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        existing_instances = Configuration.objects.count()
        if existing_instances < 1:
            super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}"
