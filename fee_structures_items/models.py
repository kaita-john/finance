from django.db import models

from fee_structures.models import FeeStructure
from schoolgroups.models import SchoolGroup
from utils import ParentModel
from voteheads.models import VoteHead


# Create your models here.
class FeeStructureItem(ParentModel):
    votehead = models.ForeignKey(VoteHead, null=True, default=None, on_delete=models.CASCADE, related_name="fee_structure_items")
    boardingStatus = models.CharField(max_length=255, blank=True, null=True)
    school_group = models.ForeignKey(SchoolGroup, null=True, default=None, on_delete=models.CASCADE, related_name="fee_structure_items")
    fee_Structure = models.ForeignKey(FeeStructure, null=True, default=None, on_delete=models.CASCADE, related_name="fee_structure_items")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    school_id = models.UUIDField(null=True, blank=True, default=None, max_length=255)

    def __str__(self):
        return f"{self.school_id}"



