from django.db import models
from django.db.models import DO_NOTHING
from rest_framework.exceptions import ValidationError

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
    admission_number = models.CharField(max_length=20)
    date_of_admission = models.CharField(max_length=255, null=True, default="None")
    guardian_name = models.CharField(max_length=255)
    guardian_phone = models.CharField(max_length=15)
    boarding_status = models.CharField(max_length=255, default="BOARDING")
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    current_Stream = models.ForeignKey(Stream, default=None, null=True, on_delete=DO_NOTHING, related_name="students")
    current_Class = models.ForeignKey(Classes, default=None, null=True, on_delete=DO_NOTHING, related_name="students")
    current_Year = models.ForeignKey(AcademicYear, default=None, null=True, on_delete=DO_NOTHING, related_name="students")
    current_Term = models.ForeignKey(Term, default=None, null=True, on_delete=DO_NOTHING, related_name="students")
    groups = models.JSONField(default=list, blank=True, null=True)
    invoice_Student = models.BooleanField(default=False, null=True)

    def save(self, *args, **kwargs):
        if self.first_name:
            self.first_name = self.first_name.upper()
        if self.last_name:
            self.last_name = self.last_name.upper()
        if self.gender:
            self.gender = self.gender.upper()
        if self.guardian_name:
            self.guardian_name = self.guardian_name.upper()
        if self.guardian_phone:
            self.guardian_phone = self.guardian_phone.upper()
        if self.boarding_status:
            self.boarding_status = self.boarding_status.upper()
        if self.admission_number:
            # self.admission_number = self.admission_number.upper()
            existing_student = Student.objects.filter(admission_number=self.admission_number,school_id=self.school_id).exclude(pk=self.pk).first()
            if existing_student:
                raise ValidationError({'detail': 'Student with the same admission number and school_id already exists.'})

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"


