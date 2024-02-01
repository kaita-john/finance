from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import DO_NOTHING

from models import ParentModel
from school.models import School


class PaymentMethod(ParentModel):
    name = models.CharField(max_length=255)
    is_cash = models.BooleanField(default=False, null=True)
    is_bank = models.BooleanField(default=False, null=True)
    is_cheque = models.BooleanField(default=False, null=True)
    school = models.ForeignKey(School, default=None, null=True, on_delete=DO_NOTHING, related_name="paymentmethods")
    is_mpesa_default = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        if not any([self.is_cash, self.is_bank, self.is_cheque, self.is_mpesa_default]):
            raise ValidationError('Select at least one payment method (is_cash, is_bank, or is_cheque, is_mpesa_default).')

        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
