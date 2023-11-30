from django.db import models

from utils import ParentModel


class Currency(ParentModel):
    currency_name = models.CharField(max_length=255)
    currency_code = models.CharField(max_length=255, unique=False)
    is_default = models.BooleanField(default=False)
    school = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.is_default:
            Currency.objects.exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.currency_name
