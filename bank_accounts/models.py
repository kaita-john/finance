from django.db import models

from account_types.models import AccountType
from currencies.models import Currency
from models import ParentModel


class BankAccount(ParentModel):
    account_name = models.CharField(max_length=255)
    account_number = models.CharField(max_length=255, unique=True)
    bank = models.CharField(max_length=255)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name="account_type")
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="currency")
    balance = models.DecimalField(max_digits=15, decimal_places=2)
    is_default = models.BooleanField(default=False)
    school = models.UUIDField(max_length=255, blank=True, null=True)
    def __str__(self):
        return self.account_name
