from django.db import models

from academic_year.models import AcademicYear
from account_types.models import AccountType
from bank_accounts.models import BankAccount
from currencies.models import Currency
from models import ParentModel
from payment_methods.models import PaymentMethod
from students.models import Student
from term.models import Term


class Receipt(ParentModel):
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="receipts")
    receipt_date = models.DateField(auto_now_add=True, null=True)
    receipt_No = models.CharField(max_length=255, null=True)
    totalAmount = models.DecimalField(max_digits=15, decimal_places=2)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name="receipts")
    bank_account = models.ForeignKey(BankAccount, on_delete=models.CASCADE, related_name="receipts")
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE, related_name="receipts")
    transaction_code = models.CharField(max_length=255, null=True, unique=True)
    addition_notes = models.TextField()
    currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name="receipts")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="receipts")
    year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="receipts")
    is_reversed = models.BooleanField(default=False, blank=False, null=False)
    reversal_date = models.DateField(null=True)

    def __str__(self):
        return f"Receipt #{self.receipt_date} - {self.student.first_name}"



