from django.db import models

from utils import ParentModel


class Stream(ParentModel):
    streamname = models.CharField(max_length=255)
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.streamname}"
