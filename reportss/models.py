from _decimal import Decimal
from django.db import models
from django.db.models import Sum, DO_NOTHING
from django.db.models.functions import Coalesce

from classes.models import Classes
from currencies.models import Currency
from financial_years.models import FinancialYear
from invoices.models import Invoice
from models import ParentModel
from payment_in_kind_Receipt.models import PIKReceipt
from receipts.models import Receipt
from students.models import Student
from django.db.models import Sum, Value, DecimalField


class ReportStudentBalance(ParentModel):
    admission_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    current_Class = models.ForeignKey(Classes, default=None, null=True, on_delete=DO_NOTHING, related_name="reportStudentBalance")
    boarding_status = models.CharField(max_length=255, default="BOARDING")
    expected = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    paid = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    totalBalance = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    schoolFee = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        if self.boarding_status:
            self.boarding_status = self.boarding_status.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"({self.id})"



class StudentTransactionsPrintView(ParentModel):
    transactionDate = models.CharField(max_length=20, null=True, blank=True)
    transactionType = models.CharField(max_length=20, null=True, blank=True)
    description = models.CharField(max_length=20, null=True, blank=True)
    expected = models.CharField(max_length=20, null=True, blank=True)
    paid = models.CharField(max_length=20, null=True, blank=True)



class IncomeSummary(ParentModel):
    votehead_name = models.CharField(max_length=20, null=True, blank=True)
    amount = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)


class ReceivedCheque(ParentModel):
    transactionDate = models.CharField(max_length=20, null=True, blank=True)
    dateofcreation = models.CharField(max_length=20, null=True, blank=True)
    chequeNo = models.CharField(max_length=20, null=True, blank=True)
    student = models.ForeignKey(Student, default=None, null=True, on_delete=DO_NOTHING)
    currency = models.ForeignKey(Currency, default=None, null=True, on_delete=DO_NOTHING)
    amount = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)






class BalanceTracker(ParentModel):
    balanceBefore = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    amountPaid = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    balanceAfter = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    student = models.ForeignKey(Student, default=None, null=True, on_delete=DO_NOTHING)
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"({self.id})"



def trackBalance(student, school_id, amount, operation, term, year):
    try:

        invoicedAmount = Invoice.objects.filter(student_id=student.id,school_id=school_id,term=term,year=year).aggregate(invoiced_amount=Coalesce(Sum('amount', output_field=DecimalField()), Value(Decimal('0.0'))))['invoiced_amount']
        receiptAmount = Receipt.objects.filter(student_id=student.id,school_id=school_id,term=term,year=year).aggregate(receipt_amount=Coalesce(Sum('totalAmount', output_field=DecimalField()), Value(Decimal('0.0'))))['receipt_amount']
        pikreceiptAmount = PIKReceipt.objects.filter(student_id=student.id,school_id=school_id,term=term,year=year).aggregate(pikreceipt_amount=Coalesce(Sum('totalAmount', output_field=DecimalField()), Value(Decimal('0.0'))))['pikreceipt_amount']

        previouslyPaidAmount = Decimal(receiptAmount) + Decimal(pikreceiptAmount)

        balanceBefore = Decimal("0.0")
        balanceAfter = Decimal("0.0")

        if operation == "plus":
            balanceBefore = invoicedAmount - previouslyPaidAmount
            amount = amount
            balanceAfter = invoicedAmount - (previouslyPaidAmount + amount)
            print(f"Invoiced amount is {invoicedAmount}, previously paid {previouslyPaidAmount}, balancebefore is {balanceBefore}  amount is {amount}")

        if operation == "minus":
            balanceBefore = invoicedAmount - previouslyPaidAmount
            amount = amount
            balanceAfter = invoicedAmount - (previouslyPaidAmount - amount)
            print(f"Invoiced amount is {invoicedAmount}, previously paid {previouslyPaidAmount}, balancebefore is {balanceBefore}  amount is {amount}")


        tracker = BalanceTracker(
            balanceBefore=balanceBefore,
            amountPaid=amount,
            balanceAfter=balanceAfter,
            student=student,
            school_id=school_id
        )
        tracker.save()

        return True

    except Exception as exception:
        raise ValueError(f"{str(exception)}")








class OpeningClosingBalances(ParentModel):
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    financial_year = models.ForeignKey(FinancialYear, default=None, null=True, on_delete=DO_NOTHING)

    opening_cash_at_hand = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    opening_cash_at_bank = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    opening_balance = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)

    closing_cash_at_hand = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    closing_cash_at_bank = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    closing_balance = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)

    def __str__(self):
        return f"({self.id})"