from django.db import models
from django.db.models import DO_NOTHING

from payment_in_kind_Receipt.models import PIKReceipt
from students.models import Student
from voteheads.models import VoteHead


class PaymentInKind(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="paymentinkinds")
    transaction_date = models.DateField(auto_now_add=True, null=True)
    receipt = models.ForeignKey(PIKReceipt, on_delete=DO_NOTHING, default=None, null=True, related_name="paymentinkinds")
    quantity = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    amount = models.DecimalField(max_digits=15, decimal_places=2, null=True)
    unit_cost = models.DecimalField(max_digits=15, decimal_places=2)
    votehead = models.ForeignKey(VoteHead, on_delete=DO_NOTHING, related_name="paymentinkinds")
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    itemName = models.CharField(max_length=255, null=True, default="None", blank=True)

    def save(self, *args, **kwargs):
        if self.itemName:
            self.itemName = self.itemName.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Receipt #{self.receipt.receipt_No} - {self.student.first_name}"



