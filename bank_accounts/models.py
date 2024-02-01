from django.db import models
from django.db.models import DO_NOTHING
from rest_framework.exceptions import ValidationError

from account_types.models import AccountType
from currencies.models import Currency
from models import ParentModel


class BankAccount(ParentModel):
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255)
    bank = models.CharField(max_length=255)
    account_type = models.ForeignKey(AccountType, on_delete=DO_NOTHING, related_name="account_type")
    currency = models.ForeignKey(Currency, on_delete=DO_NOTHING, related_name="currency")
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    is_default = models.BooleanField(default=False)
    school = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.account_name:
            self.account_name = self.account_name.upper()
        if self.account_number:
            self.account_number = self.account_number.upper()
            existing_account = BankAccount.objects.filter(account_number=self.account_number,school=self.school).exclude(pk=self.pk).first()
            if existing_account:
                raise ValidationError( {'Bank account with the same account number and school already exists.'})
        if self.is_default:
            BankAccount.objects.filter(school=self.school).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.account_name
