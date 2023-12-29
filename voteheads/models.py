from django.db import models
from django.db.models import DO_NOTHING
from rest_framework.exceptions import ValidationError

from account_types.models import AccountType
from constants import AUTO_CONFIGURATION_CHOICES, CONFIGURATION_CHOICES, MANUAL, AUTO
from models import ParentModel


class VoteHead(ParentModel):
    vote_head_name = models.CharField(max_length=255)
    folio_number = models.CharField(max_length=255, null=True, default=1)
    exempted = models.BooleanField(default=False, blank=False, null=False)
    account_type = models.ForeignKey(AccountType, on_delete=DO_NOTHING, related_name='voteheads')
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    is_Overpayment_Default = models.BooleanField(default=False, blank=False, null=False)
    is_Arrears_Default = models.BooleanField(default=False, blank=False, null=False)
    priority_number = models.CharField(max_length=255,  default=1)
    ledget_folio_number_lf = models.CharField(max_length=255,  default=1)

    def save(self, *args, **kwargs):
        if self.is_Overpayment_Default:
            VoteHead.objects.exclude(pk=self.pk).update(is_Overpayment_Default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.vote_head_name} - {self.id}"




class VoteheadConfiguration(ParentModel):
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    configuration_type = models.CharField(max_length=10, choices=CONFIGURATION_CHOICES)
    auto_configuration_type = models.CharField(max_length=10, choices=AUTO_CONFIGURATION_CHOICES, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.configuration_type == MANUAL:
            self.auto_configuration_type = None
        elif self.configuration_type == AUTO and not self.auto_configuration_type:
            raise ValidationError("Auto Configuration type must be specified")

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.configuration_type}-{self.auto_configuration_type}"


