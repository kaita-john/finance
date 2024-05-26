from django.db import models

from models import ParentModel


class Stream(ParentModel):
    streamname = models.CharField(max_length=255)
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.streamname:
            self.streamname = self.streamname.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.streamname}"
