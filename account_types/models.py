from django.db import models

from models import ParentModel


class AccountType(ParentModel):
    account_type_name = models.CharField(max_length=255)
    is_default = models.BooleanField(default=False)
    school = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.account_type_name:
            self.account_type_name = self.account_type_name.upper()
        if self.is_default:
            AccountType.objects.filter(school=self.school).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)
    def __str__(self):
        return self.account_type_name
