from django.db import models

from account_types.models import AccountType
from financial_years.models import FinancialYear
from models import ParentModel


class Budget(ParentModel):
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    accountType = models.ForeignKey(AccountType, default=None, null=True, on_delete=models.CASCADE, related_name="budgets")
    financialYear = models.ForeignKey(FinancialYear, default=None, null=True, on_delete=models.CASCADE, related_name="budgets")
    budget_items = models.JSONField(default=list, blank=True, null=True)

    def __str__(self):
        return f"{self.id}"
