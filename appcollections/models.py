from django.db import models
from django.db.models import DO_NOTHING

from receipts.models import Receipt
from students.models import Student
from voteheads.models import VoteHead


class Collection(models.Model):
    student = models.ForeignKey(Student, on_delete=DO_NOTHING, related_name="collections")
    transaction_date = models.DateField(auto_now_add=True, null=True)
    receipt = models.ForeignKey(Receipt, on_delete=DO_NOTHING, default=None, null=True, related_name="collections")
    amount = models.DecimalField(max_digits=15, decimal_places=2)
    votehead = models.ForeignKey(VoteHead, on_delete=DO_NOTHING, related_name="collections")
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    is_overpayment = models.BooleanField(default=False, null=True)

    def __str__(self):
        return f"Collection #{self.id} - {self.student.first_name}"



