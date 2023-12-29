from django.db import models
from django.db.models import DO_NOTHING

from academic_year.models import AcademicYear
from classes.models import Classes
from schoolgroups.models import SchoolGroup
from streams.models import Stream
from term.models import Term
from models import ParentModel


class Student(ParentModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=6, default="BOY")
    admission_number = models.CharField(max_length=20, unique=True)
    date_of_admission = models.DateField(blank=True, null=True)
    guardian_name = models.CharField(max_length=255)
    guardian_phone = models.CharField(max_length=15)
    boarding_status = models.CharField(max_length=255, default="BOARDING")
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    current_Stream = models.ForeignKey(Stream, default=None, null=True, on_delete=DO_NOTHING, related_name="students")
    current_Class = models.ForeignKey(Classes, default=None, null=True, on_delete=DO_NOTHING, related_name="students")
    current_Year = models.ForeignKey(AcademicYear, default=None, null=True, on_delete=DO_NOTHING, related_name="students")
    current_Term = models.ForeignKey(Term, default=None, null=True, on_delete=DO_NOTHING, related_name="students")
    group = models.ForeignKey(SchoolGroup, default=None, null=True, on_delete=DO_NOTHING, related_name="students")
    invoice_Student = models.BooleanField(default=False, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"


