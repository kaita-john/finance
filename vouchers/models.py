from django.db import models

from account_types.models import AccountType
from bank_accounts.models import BankAccount
from configurations.models import Configuration
from expense_categories.models import ExpenseCategory
from financial_years.models import FinancialYear
from models import ParentModel
from payment_methods.models import PaymentMethod
from staff.models import Staff
from suppliers.models import Supplier


# models.py
class Voucher(ParentModel):
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    accountType = models.ForeignKey(AccountType, default=None, null=True, on_delete=models.CASCADE, related_name="vouchers")
    recipientType = models.CharField(max_length=255, blank=True, null=True)
    staff = models.ForeignKey(Staff, default=None, null=True, on_delete=models.SET_NULL, related_name="vouchers")
    supplier = models.ForeignKey(Supplier, default=None, null=True, on_delete=models.SET_NULL, related_name="vouchers")
    other = models.CharField(max_length=255, blank=True, null=True)

    bank_account = models.ForeignKey(BankAccount, null=True, on_delete=models.SET_NULL, related_name="vouchers")
    payment_Method = models.ForeignKey(PaymentMethod, null=True, on_delete=models.SET_NULL, related_name="vouchers")
    expenseCategory = models.ForeignKey(ExpenseCategory, null=True, default=None, on_delete=models.SET_NULL, related_name="vouchers")

    referenceNumber = models.CharField(max_length=255, blank=True, null=True)
    paymentDate = models.DateField(null=True)

    paymentVoucherNumber = models.CharField(max_length=255, blank=True, null=True)
    description = models.CharField(max_length=7000, blank=True, null=True)
    totalAmount = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    deliveryNoteNumber = models.CharField(max_length=255, blank=True, null=True)
    referallNumber = models.CharField(max_length=255, blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    date_deleted = models.DateTimeField(null=True)

    financial_year = models.ForeignKey(FinancialYear, null=True, on_delete=models.SET_NULL, related_name="vouchers")
    counter = models.FloatField(null=True, default=None)

    def save(self, *args, **kwargs):
        if self.recipientType:
            self.recipientType = self.recipientType.upper()
        if self.other:
            self.other = self.other.upper()
        if self.referenceNumber:
            # self.referenceNumber = self.referenceNumber.upper()
            pass
        if self.paymentVoucherNumber:
            self.paymentVoucherNumber = self.paymentVoucherNumber.upper()
        if self.deliveryNoteNumber:
            self.deliveryNoteNumber = self.deliveryNoteNumber.upper()

        if not self.counter:
            school_id_filter = {'school_id': self.school_id}  # Add school filter here
            school_filter = {'school': self.school_id}  # Add school filter here

            if Voucher.objects.filter(**school_id_filter).count() == 0:
                start_at_value = Configuration.objects.filter(**school_filter).values('voucher_start_at').first().get(
                    'voucher_start_at', 1)
                self.counter = start_at_value
            else:
                max_counter = Voucher.objects.filter(**school_id_filter).aggregate(models.Max('counter'))['counter__max']
                self.counter = max_counter + 1 if max_counter is not None else 1

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.id}"