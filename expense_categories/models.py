from django.db import models
from models import ParentModel

class ExpenseCategory(ParentModel):
    name = models.CharField(max_length=255)
    school = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.id)
