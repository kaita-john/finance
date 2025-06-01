from django.db import models
from django.db.models import DO_NOTHING, CASCADE

from fee_structures.models import FeeStructure
from models import ParentModel
from schoolgroups.models import SchoolGroup
from voteheads.models import VoteHead


# Create your models here.
class FeeStructureItem(ParentModel):
    votehead = models.ForeignKey(VoteHead, null=True, default=None, on_delete=CASCADE, related_name="fee_structure_items")
    boardingStatus = models.CharField(max_length=255, blank=True, null=True)
    school_group = models.ForeignKey(SchoolGroup, null=True, default=None, on_delete=CASCADE, related_name="fee_structure_items")
    fee_Structure = models.ForeignKey(FeeStructure, null=True, default=None, on_delete=CASCADE, related_name="fee_structure_items")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    school_id = models.UUIDField(null=True, blank=True, default=None, max_length=255)

    def save(self, *args, **kwargs):
        if self.boardingStatus:
            self.boardingStatus = self.boardingStatus.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}"



