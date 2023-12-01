from django.db import models

from academic_year.models import AcademicYear
from classes.models import Classes
from schoolgroups.models import SchoolGroup
from term.models import Term
from utils import ParentModel
from voteheads.models import VoteHead


# Create your models here.
class FeeStructureItem(ParentModel):
    votehead = models.ForeignKey(VoteHead, on_delete=models.CASCADE, related_name="fee_structures_items")
    boardingStatus = models.CharField(max_length=255, blank=True, null=True)
    school_group = models.ForeignKey(SchoolGroup, on_delete=models.CASCADE, related_name="fee_structures_items")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    school_id = models.UUIDField(max_length=255)
    def __str__(self):
        return f"{self.votehead.vote_head_name} - {self.boardingStatus} - {self.school_group.name}"





