import json

from django.db import models
from django.db.models import DO_NOTHING

from academic_year.models import AcademicYear
from bank_accounts.models import BankAccount
from currencies.models import Currency
from models import ParentModel
from payment_methods.models import PaymentMethod
from schoolgroups.models import SchoolGroup
from term.models import Term


class Grant(ParentModel):
    bankAccount = models.ForeignKey(BankAccount, default=None, on_delete=DO_NOTHING, related_name="grants")
    paymentMethod = models.ForeignKey(PaymentMethod, null=True, on_delete=DO_NOTHING, related_name="grants")
    transactionNumber = models.CharField(max_length=255, default=None)
    receipientAddress = models.CharField(max_length=255, default=None)
    institution = models.CharField(max_length=255, default=None)
    institutionAddress = models.CharField(max_length=255, default=None)
    term = models.ForeignKey(Term, default=None, on_delete=DO_NOTHING, related_name="grants")
    year = models.ForeignKey(AcademicYear, default=None, null=True, on_delete=DO_NOTHING, related_name="grants")
    school_id = models.UUIDField(max_length=255, default=None, blank=True, null=True)
    deleted = models.BooleanField(default=False, null=True)
    deleted_date = models.DateField(null=True)
    receipt_date = models.DateField(default=None, null=True)
    schoolgroup = models.ForeignKey(SchoolGroup, default=None, null=True, on_delete=DO_NOTHING, related_name="grants")
    currency = models.ForeignKey(Currency, default=None, null=True, on_delete=DO_NOTHING, related_name="grants")
    studentamount = models.DecimalField(max_digits=15, null=True, default=0.00, decimal_places=2)
    students = models.JSONField(default=list)
    voteheadamounts = models.JSONField(default=dict, blank=True, null=True)
    overall_amount = models.DecimalField(max_digits=15, null=True,blank=True, default=0.00, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.receipientAddress:
            self.receipientAddress = self.receipientAddress.upper()
        if self.institution:
            self.institution = self.institution.upper()
        if self.institutionAddress:
            self.institutionAddress = self.institutionAddress.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}"





