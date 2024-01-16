from django.db import models
from django.db.models import DO_NOTHING

from academic_year.models import AcademicYear
from bank_accounts.models import BankAccount
from classes.models import Classes
from currencies.models import Currency
from financial_years.models import FinancialYear
from models import ParentModel
from receipts.models import Receipt
from students.models import Student
from term.models import Term
from voteheads.models import VoteHead


class PIKReceipt(ParentModel):
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=DO_NOTHING, related_name="pik_receipts")
    receipt_date = models.DateField(auto_now_add=True, null=True)
    receipt_No = models.CharField(max_length=255, null=True)
    term = models.ForeignKey(Term, null=True, on_delete=DO_NOTHING, related_name="pik_receipts")
    year = models.ForeignKey(AcademicYear, null=True, on_delete=DO_NOTHING, related_name="pik_receipts")
    currency = models.ForeignKey(Currency, null=True, on_delete=DO_NOTHING, related_name="pik_receipts")
    totalAmount = models.DecimalField(max_digits=15, null=True, decimal_places=2)
    bank_account = models.ForeignKey(BankAccount, on_delete=DO_NOTHING, related_name="pik_receipts")
    addition_notes = models.CharField(max_length=7000, blank=True, null=True)
    is_posted = models.BooleanField(default=True, blank=True, null=False)
    unposted_date = models.DateField(null=True)
    student_class = models.ForeignKey(Classes, null=True, on_delete=DO_NOTHING, related_name="pik_receipts")
    overpayment_amount = models.DecimalField(max_digits=15, default=0.00, null=True, blank=True, decimal_places=2)
    financial_year = models.ForeignKey(FinancialYear, null=True, on_delete=DO_NOTHING, related_name="pik_receipts")
    counter = models.FloatField(null=True, default=None)

    def save(self, *args, **kwargs):
        if self.receipt_No:
            self.receipt_No = self.receipt_No.upper()
        if not self.counter:
            max_counter = PIKReceipt.objects.all().aggregate(models.Max('counter'))['counter__max']
            self.counter = max_counter + 1 if max_counter is not None else 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"PaymentInKind Receipt {self.id} - {self.receipt_date} - {self.student.first_name}"



