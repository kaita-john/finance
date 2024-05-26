from django.db import models

from models import ParentModel


# Create your models here.
class SchoolGroup(ParentModel):
    name = models.CharField(max_length=255)
    school_id = models.UUIDField(max_length=255, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        super().save(*args, **kwargs)
    def __str__(self):
        return self.name





