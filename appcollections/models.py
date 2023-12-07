from django.db import models

from academic_year.models import AcademicYear
from account_types.models import AccountType
from bank_accounts.models import BankAccount
from currencies.models import Currency
from payment_methods.models import PaymentMethod
from receipts.models import Receipt
from students.models import Student
from term.models import Term
from voteheads.models import VoteHead


class Collection(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="collections")
    transaction_date = models.DateField(auto_now_add=True, null=True)
    receipt = models.ForeignKey(Receipt, on_delete=models.CASCADE, default=None, null=True, related_name="collections")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    votehead = models.ForeignKey(VoteHead, on_delete=models.CASCADE, related_name="collections")
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Receipt #{self.receipt.receipt_No} - {self.student.first_name}"



