from django.db import models

from academic_year.models import AcademicYear
from classes.models import Classes
from term.models import Term
from utils import ParentModel


# Create your models here.
class FeeStructure(ParentModel):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="fee_structures")
    classes = models.ForeignKey(Classes, on_delete=models.CASCADE, related_name="fee_structures")
    term = models.ForeignKey(Term, on_delete=models.CASCADE, related_name="fee_structures")
    instructions = models.CharField(max_length=255, blank=True, null=True)
    school_id = models.UUIDField(max_length=255)
    def __str__(self):
        return f"{self.academic_year} - {self.classes} - {self.term}"





