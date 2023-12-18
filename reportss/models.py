from django.db import models

from classes.models import Classes
from models import ParentModel


class ReportStudentBalance(ParentModel):
    admission_number = models.CharField(max_length=20, unique=True)
    name = models.CharField(max_length=255)
    current_Class = models.ForeignKey(Classes, default=None, null=True, on_delete=models.CASCADE, related_name="reportStudentBalance")
    boarding_status = models.CharField(max_length=255, default="BOARDING")
    expected = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    paid = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    totalBalance = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    schoolFee = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)

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

