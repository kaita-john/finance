from django.db import models
from django.db.models import DO_NOTHING

from academic_year.models import AcademicYear
from bank_accounts.models import BankAccount
from configurations.models import Configuration
from currencies.models import Currency
from financial_years.models import FinancialYear
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
    assigned_voteheadamounts = models.JSONField(default=dict, blank=True, null=True)
    overall_amount = models.DecimalField(max_digits=15, null=True,blank=True, default=0.00, decimal_places=2)
    financial_year = models.ForeignKey(FinancialYear, null=True, on_delete=DO_NOTHING, related_name="grants")
    counter = models.FloatField(null=True, default=None)

    def save(self, *args, **kwargs):
        if self.receipientAddress:
            self.receipientAddress = self.receipientAddress.upper()
        if self.institution:
            self.institution = self.institution.upper()
        if self.institutionAddress:
            self.institutionAddress = self.institutionAddress.upper()

        if not self.counter:
            school_filter = {'school_id': self.school_id}  # Add school filter here
            schooltwo_filter = {'school': self.school_id}  # Add school filter here
            if Grant.objects.filter(**school_filter).count() == 0:
                start_at_value = Configuration.objects.filter(**schooltwo_filter).values('grant_start_at').first().get(
                    'grant_start_at', 1)
                self.counter = start_at_value
            else:
                max_counter = Grant.objects.filter(**school_filter).aggregate(models.Max('counter'))['counter__max']
                self.counter = max_counter + 1 if max_counter is not None else 1

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.id}"





