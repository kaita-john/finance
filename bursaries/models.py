from django.db import models

from academic_year.models import AcademicYear
from bank_accounts.models import BankAccount
from models import ParentModel
from payment_methods.models import PaymentMethod
from term.models import Term


class Bursary(ParentModel):
    bankAccount = models.ForeignKey(BankAccount, default=None, on_delete=models.CASCADE, related_name="bursaries")
    paymentMethod = models.ForeignKey(PaymentMethod, null=True, on_delete=models.CASCADE, related_name="bursaries")
    transactionNumber = models.CharField(max_length=255, default=None)
    receipientAddress = models.CharField(max_length=255, default=None)
    institution = models.CharField(max_length=255, default=None)
    institutionAddress = models.CharField(max_length=255, default=None)
    term = models.ForeignKey(Term, default=None, on_delete=models.CASCADE, related_name="bursaries")
    year = models.ForeignKey(AcademicYear, default=None, null=True, on_delete=models.CASCADE, related_name="bursaries")
    school_id = models.UUIDField(max_length=255, default=None, blank=True, null=True)
    posted = models.BooleanField(default=False, null=True)
    unposted_date = models.DateField(null=True)


    def __str__(self):
        return f"{self.id}"

