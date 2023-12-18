import uuid

from django.db import models

class ParentModel(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    dateofcreation = models.DateField(auto_now_add=True, null=True)

    class Meta:
        abstract = True