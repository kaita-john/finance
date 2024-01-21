from django.db import models
from django.db.models import DO_NOTHING

from academic_year.models import AcademicYear
from account_types.models import AccountType
from bank_accounts.models import BankAccount
from classes.models import Classes
from configurations.models import Configuration
from currencies.models import Currency
from financial_years.models import FinancialYear
from models import ParentModel
from payment_methods.models import PaymentMethod
from students.models import Student
from term.models import Term


class Receipt(ParentModel):
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=DO_NOTHING, related_name="receipts")
    receipt_date = models.DateField(auto_now_add=True, null=True)
    receipt_No = models.CharField(max_length=255, null=True)
    totalAmount = models.DecimalField(max_digits=15, decimal_places=2)
    account_type = models.ForeignKey(AccountType, on_delete=DO_NOTHING, related_name="receipts")
    bank_account = models.ForeignKey(BankAccount, on_delete=DO_NOTHING, related_name="receipts")
    payment_method = models.ForeignKey(PaymentMethod, null=True, default=None, on_delete=DO_NOTHING, related_name="receipts")
    term = models.ForeignKey(Term, null=True, on_delete=DO_NOTHING, related_name="receipts")
    year = models.ForeignKey(AcademicYear, null=True, on_delete=DO_NOTHING, related_name="receipts")
    currency = models.ForeignKey(Currency, null=True, on_delete=DO_NOTHING, related_name="receipts")
    transaction_code = models.CharField(max_length=255, null=True)
    transaction_date = models.DateField(null=True, default=None)
    addition_notes = models.CharField(max_length=7000, blank=True, null=True)
    is_reversed = models.BooleanField(default=False, blank=False, null=False)
    reversal_date = models.DateField(null=True)
    student_class = models.ForeignKey(Classes, null=True, on_delete=DO_NOTHING, related_name="receipts")
    financial_year = models.ForeignKey(FinancialYear, null=True, on_delete=DO_NOTHING, related_name="receipts")
    counter = models.FloatField(null=True, default=None)

    def save(self, *args, **kwargs):
        if self.receipt_No:
            self.receipt_No = self.receipt_No.upper()

        if not self.counter:
            if Receipt.objects.count() == 0:
                start_at_value = Configuration.objects.values('receipt_start_at').first().get('receipt_start_at', 1)
                self.counter = start_at_value
            else:
                from payment_in_kind_Receipt.models import PIKReceipt
                max_counter_receipt = Receipt.objects.all().aggregate(models.Max('counter'))['counter__max']
                max_counter_pik_receipt = PIKReceipt.objects.all().aggregate(models.Max('counter'))['counter__max']
                self.counter = max(max_counter_receipt, max_counter_pik_receipt) + 1

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.receipt_date} - {self.student.first_name}"



