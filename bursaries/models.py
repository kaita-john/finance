from django.db import models
from django.db.models import DO_NOTHING

from academic_year.models import AcademicYear
from bank_accounts.models import BankAccount
from classes.models import Classes
from configurations.models import Configuration
from currencies.models import Currency
from financial_years.models import FinancialYear
from models import ParentModel
from payment_methods.models import PaymentMethod
from schoolgroups.models import SchoolGroup
from term.models import Term
from voteheads.models import VoteHead


class Bursary(ParentModel):
    bankAccount = models.ForeignKey(BankAccount, default=None, on_delete=DO_NOTHING, related_name="bursaries")
    paymentMethod = models.ForeignKey(PaymentMethod, null=True, on_delete=DO_NOTHING, related_name="bursaries")
    transactionNumber = models.CharField(max_length=255, default=None)
    receipientAddress = models.CharField(max_length=255, default=None)
    institution = models.CharField(max_length=255, default=None)
    institutionAddress = models.CharField(max_length=255, default=None)
    term = models.ForeignKey(Term, default=None, on_delete=DO_NOTHING, related_name="bursaries")
    year = models.ForeignKey(AcademicYear, default=None, null=True, on_delete=DO_NOTHING, related_name="bursaries")
    school_id = models.UUIDField(max_length=255, default=None, blank=True, null=True)
    posted = models.BooleanField(default=False, null=True)
    unposted_date = models.DateField(null=True)
    receipt_date = models.DateField(default=None, null=True)
    financial_year = models.ForeignKey(FinancialYear, default=None, null=True, on_delete=models.CASCADE, related_name="bursaries")
    schoolgroup = models.ForeignKey(SchoolGroup, default=None, null=True, on_delete=DO_NOTHING, related_name="bursaries")
    votehead = models.ForeignKey(VoteHead, default=None, null=True, on_delete=DO_NOTHING, related_name="bursaries")
    classes = models.ForeignKey(Classes, default=None, null=True, on_delete=DO_NOTHING, related_name="bursaries")
    currency = models.ForeignKey(Currency, default=None, null=True, on_delete=DO_NOTHING, related_name="bursaries")
    studentamount = models.DecimalField(max_digits=15, null=True, default=0.00, decimal_places=2)
    counter = models.FloatField(null=True, default=None)

    def save(self, *args, **kwargs):
        if self.institution:
            self.institution = self.institution.upper()
        if self.institutionAddress:
            self.institutionAddress = self.institutionAddress.upper()

        if not self.counter:
            school_filter = {'school_id': self.school_id}
            schooltwo_filter = {'school': self.school_id}

            if Bursary.objects.filter(**school_filter).count() == 0:
                start_at_value = Configuration.objects.filter(**schooltwo_filter).values('bursary_start_at').first().get(
                    'bursary_start_at', 1)
                self.counter = start_at_value
            else:
                max_counter = Bursary.objects.filter(**school_filter).aggregate(models.Max('counter'))['counter__max']
                self.counter = max_counter + 1 if max_counter is not None else 1

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.id}"

