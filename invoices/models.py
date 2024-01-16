from django.db import models
from django.db.models import DO_NOTHING

from academic_year.models import AcademicYear
from classes.models import Classes
from currencies.models import Currency
from schoolgroups.models import SchoolGroup
from streams.models import Stream
from students.models import Student
from term.models import Term
from models import ParentModel
from voteheads.models import VoteHead

class Balance(models.Model):
    structure_year = models.ForeignKey(AcademicYear, on_delete=DO_NOTHING)
    structure_term = models.ForeignKey(Term, on_delete=DO_NOTHING)


class Uninvoice(models.Model):
    structure_year = models.ForeignKey(AcademicYear, default=None, null=True, on_delete=DO_NOTHING)
    structure_term = models.ForeignKey(Term, null=True, default=None, on_delete=DO_NOTHING)
    structure_class = models.ForeignKey(Classes, null=True, default=None, on_delete=DO_NOTHING)
    structure_stream = models.ForeignKey(Stream, null=True, default=None, on_delete=DO_NOTHING)
    student = models.ForeignKey(Student, null=True, default=None, on_delete=DO_NOTHING, related_name="innovation_document_creator")
    filter_type = models.CharField(max_length=255, null=True, default="classes")


class Structure(models.Model):
    structure_year = models.ForeignKey(AcademicYear, on_delete=DO_NOTHING)
    structure_term = models.ForeignKey(Term, on_delete=DO_NOTHING)
    structure_class = models.ForeignKey(Classes, on_delete=DO_NOTHING)
    filter_type =  models.CharField(max_length=255)
    student = models.ForeignKey(Student, default=None, null=True, on_delete=DO_NOTHING, related_name="structures")
    classes = models.ForeignKey(Classes, default=None, null=True, on_delete=DO_NOTHING, related_name="structures")
    stream = models.ForeignKey(Stream, default=None, null=True, on_delete=DO_NOTHING, related_name="structures")
    group = models.ForeignKey(SchoolGroup, default=None, null=True, on_delete=DO_NOTHING, related_name="structures")


class Invoice(ParentModel):
    issueDate = models.CharField(max_length=255)
    invoiceNo = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    paid = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    due = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    description = models.CharField(max_length=255)
    student = models.ForeignKey(Student, default=None, null=True, on_delete=DO_NOTHING, related_name="invoices")
    votehead = models.ForeignKey(VoteHead, default=None, null=True, on_delete=DO_NOTHING, related_name="invoices")
    term = models.ForeignKey(Term, default=None, null=True, on_delete=DO_NOTHING, related_name="invoices")
    year = models.ForeignKey(AcademicYear, default=None, null=True, on_delete=DO_NOTHING, related_name="invoices")
    classes = models.ForeignKey(Classes, default=None, null=True, on_delete=DO_NOTHING, related_name="invoices")
    currency = models.ForeignKey(Currency, default=None, null=True, on_delete=DO_NOTHING, related_name="invoices")
    school_id = models.UUIDField(max_length=255, blank=True, null=True)



    def __str__(self):
        return f"{self.invoiceNo}"




