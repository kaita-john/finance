from django.db import models

from academic_year.models import AcademicYear
from classes.models import Classes
from currencies.models import Currency
from streams.models import Stream
from students.models import Student
from term.models import Term
from utils import ParentModel


class Structure(models.Model):
    structure_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE)
    structure_term = models.ForeignKey(Term, on_delete=models.CASCADE)
    structure_class = models.ForeignKey(Classes, on_delete=models.CASCADE)
    filter_type =  models.CharField(max_length=255)
    student = models.ForeignKey(Student, default=None, null=True, on_delete=models.CASCADE, related_name="structures")
    classes = models.ForeignKey(Classes, default=None, null=True, on_delete=models.CASCADE, related_name="structures")
    stream = models.ForeignKey(Stream, default=None, null=True, on_delete=models.CASCADE, related_name="structures")


class Invoice(ParentModel):
    issueDate = models.CharField(max_length=255)
    invoiceNo = models.CharField(max_length=255, unique=True)
    amount = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    paid = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    due = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    description = models.CharField(max_length=255)
    student = models.ForeignKey(Student, default=None, null=True, on_delete=models.CASCADE, related_name="invoices")
    term = models.ForeignKey(Term, default=None, null=True, on_delete=models.CASCADE, related_name="invoices")
    year = models.ForeignKey(AcademicYear, default=None, null=True, on_delete=models.CASCADE, related_name="invoices")
    classes = models.ForeignKey(Classes, default=None, null=True, on_delete=models.CASCADE, related_name="invoices")
    currency = models.ForeignKey(Currency, default=None, null=True, on_delete=models.CASCADE, related_name="invoices")
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.invoiceNo}"




