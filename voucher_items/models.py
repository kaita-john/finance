from django.db import models
from django.db.models import DO_NOTHING

from models import ParentModel
from term.models import Term
from voteheads.models import VoteHead
from vouchers.models import Voucher


# Create your models here.
class VoucherItem(ParentModel):
    school_id = models.UUIDField(null=True, blank=True, default=None, max_length=255)
    votehead = models.ForeignKey(VoteHead, null=True, default=None, on_delete=DO_NOTHING, related_name="voucher_items")
    amount = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    quantity = models.DecimalField(max_digits=15, default=0.00, decimal_places=2)
    itemName = models.CharField(max_length=255)
    voucher = models.ForeignKey(Voucher, null=True, default=None, on_delete=models.SET_NULL, related_name="voucher_items")

    def __str__(self):
        return f"{self.id}"




