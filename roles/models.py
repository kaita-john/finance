from django.db import models

from models import ParentModel


class Role(ParentModel):
    name = models.CharField(max_length=255, unique=True)
    def __str__(self):
        return self.name
