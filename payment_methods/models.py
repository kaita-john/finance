from django.db import models
from django.db.models import DO_NOTHING

from school.models import School
from models import ParentModel


class PaymentMethod(ParentModel):
    name = models.CharField(max_length=255)
    is_cash = models.BooleanField(default=False, null=True)
    is_bank = models.BooleanField(default=False, null=True)
    is_cheque = models.BooleanField(default=False, null=True)
    school = models.ForeignKey(School, default=None, null=True, on_delete=DO_NOTHING, related_name="paymentmethods")

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
