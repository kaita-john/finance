from django.db import models

from models import ParentModel


class Role(ParentModel):
    name = models.CharField(max_length=255, unique=True)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
