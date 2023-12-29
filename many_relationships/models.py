from django.db import models

from academic_year.models import AcademicYear
from classes.models import Classes
from fee_structures_items.models import FeeStructureItem
from term.models import Term
from models import ParentModel


# models.py
class Vehicle(ParentModel):
    academic_year = models.ForeignKey(AcademicYear, default=None, on_delete=DO_NOTHING, related_name="fee_structures")
    classes = models.ForeignKey(Classes, default=None, on_delete=DO_NOTHING, related_name="fee_structures")
    term = models.ForeignKey(Term, default=None, on_delete=DO_NOTHING, related_name="fee_structures")
    instructions = models.CharField(max_length=255, blank=True, null=True)
    fee_structure_items = models.ManyToManyField(FeeStructureItem, related_name="fee_structures", blank=True)
    school_id = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"{self.school_id}"