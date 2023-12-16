from django.db import models

from bank_accounts.models import BankAccount
from expense_categories.models import ExpenseCategory
from models import ParentModel
from payment_methods.models import PaymentMethod


# models.py
class Voucher(ParentModel):
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    recipientType = models.CharField(max_length=255, blank=True, null=True)
    member = models.CharField(max_length=255, blank=True, null=True)

    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="vouchers")
    payment_Method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, related_name="vouchers")
    expenseCategory = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name="vouchers")

    referenceNumber = models.CharField(max_length=255, blank=True, null=True)
    paymentDate = models.DateField(null=True)
    paymentVoucherNumber = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(null=True)
    totalAmount = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    deliveryNoteNumber = models.CharField(max_length=255, blank=True, null=True)

    is_deleted = models.BooleanField(default=False)
    date_deleted = models.DateTimeField(null=True)

    def __str__(self):
        return f"{self.id}"