from django.db import models
from django.db.models import DO_NOTHING

from grants.models import Grant
from models import ParentModel
from voteheads.models import VoteHead


class GrantItem(ParentModel):
    item_date = models.DateField(auto_now_add=True, null=True)
    votehead = models.ForeignKey(VoteHead, null=True, default=None, on_delete=DO_NOTHING, related_name="grant_items")
    grant = models.ForeignKey(Grant, null=True, default=None, on_delete=DO_NOTHING, related_name="grant_items")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    school_id = models.UUIDField(null=True, blank=True, default=None, max_length=255)

    def __str__(self):
        return f"{self.id}"


