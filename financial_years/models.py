from django.db import models

from models import ParentModel


# Create your models here.
class FinancialYear(ParentModel):
    financial_year_name = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    school = models.UUIDField(max_length=255, blank=True, null=True)
    is_current = models.BooleanField(default=False, null=True)

    def __str__(self):
        return self.financial_year_name





