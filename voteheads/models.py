from django.db import models
from django.db.models import DO_NOTHING
from rest_framework.exceptions import ValidationError

from account_types.models import AccountType
from constants import AUTO_CONFIGURATION_CHOICES, CONFIGURATION_CHOICES, MANUAL, AUTO
from models import ParentModel


class VoteHead(ParentModel):
    vote_head_name = models.CharField(max_length=255)
    folio_number = models.CharField(max_length=255, null=True, default=None)
    exempted = models.BooleanField(default=False, blank=False, null=False)
    account_type = models.ForeignKey(AccountType, on_delete=DO_NOTHING, related_name='voteheads')
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    is_Overpayment_Default = models.BooleanField(default=False, blank=False, null=False)
    is_Arrears_Default = models.BooleanField(default=False, blank=False, null=False)

    is_bursary_default = models.BooleanField(default=False, blank=False, null=False)
    priority_number = models.CharField(max_length=255,  default=None, blank=True, null=True)
    ledget_folio_number_lf = models.CharField(max_length=255,  default=None, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.folio_number:
            self.folio_number = self.folio_number.upper()
            existing_folio_head = VoteHead.objects.filter(folio_number=self.folio_number,school_id=self.school_id, account_type=self.account_type).exclude(pk=self.pk).first()
            if existing_folio_head:
                raise ValidationError({'VoteHead with the same folio number and school_id already exists.'})

        if self.priority_number:
            self.priority_number = self.priority_number.upper()
            existing_priority_head = VoteHead.objects.filter(priority_number=self.priority_number, account_type = self.account_type, school_id=self.school_id).exclude(pk=self.pk).first()
            if existing_priority_head:
                raise ValidationError({'VoteHead with the same priority number and school_id already exists.'})

        existing_votehead = VoteHead.objects.filter(vote_head_name=self.vote_head_name, folio_number=self.folio_number, priority_number=self.priority_number, account_type = self.account_type, school_id=self.school_id).exclude(pk=self.pk).first()
        if existing_votehead:
            raise ValidationError({'VoteHead with the same name and school_id already exists.'})

        if self.is_Overpayment_Default:
            VoteHead.objects.filter(school_id=self.school_id).exclude(pk=self.pk).update(is_Overpayment_Default=False)

        if self.is_Arrears_Default:
            VoteHead.objects.filter(school_id=self.school_id).exclude(pk=self.pk).update(is_Arrears_Default=False)

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


