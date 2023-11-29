from django.db import models

from streams.models import Stream
from utils import ParentModel


class Student(ParentModel):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    gender = models.CharField(max_length=6, default="BOY")
    admission_number = models.CharField(max_length=20, unique=True)
    date_of_admission = models.DateField(blank=True, null=True)
    guardian_name = models.CharField(max_length=255)
    guardian_phone = models.CharField(max_length=15)
    stream = models.ForeignKey(Stream, on_delete=models.CASCADE, related_name="students")
    boarding_status = models.CharField(max_length=255, default="BOARDING")
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.admission_number})"


