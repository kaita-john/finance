from django.db import models

from utils import ParentModel


# Create your models here.
class AcademicYear(ParentModel):
    academic_year = models.CharField(max_length=255)
    start_date = models.DateField()
    end_date = models.DateField()
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.academic_year





