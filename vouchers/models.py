from django.db import models

from bank_accounts.models import BankAccount
from expense_categories.models import ExpenseCategory
from financial_years.models import FinancialYear
from models import ParentModel
from payment_methods.models import PaymentMethod
from receipts.models import Receipt
from staff.models import Staff
from suppliers.models import Supplier


# models.py
class Voucher(ParentModel):
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

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
            self.referenceNumber = self.referenceNumber.upper()
        if self.paymentVoucherNumber:
            self.paymentVoucherNumber = self.paymentVoucherNumber.upper()
        if self.deliveryNoteNumber:
            self.deliveryNoteNumber = self.deliveryNoteNumber.upper()

        if not self.counter:
            max_counter = Voucher.objects.all().aggregate(models.Max('counter'))['counter__max']
            self.counter = max_counter + 1 if max_counter is not None else 1

        super().save(*args, **kwargs)


    def __str__(self):
        return f"{self.id}"