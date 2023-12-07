from django.db import models

from account_types.models import AccountType
from models import ParentModel


class VoteHead(ParentModel):
    vote_head_name = models.CharField(max_length=255)
    folio_number = models.CharField(max_length=255)
    exempted = models.BooleanField(default=False, blank=False, null=False)
    account_type = models.ForeignKey(AccountType, on_delete=models.CASCADE, related_name='voteheads')
    school_id = models.UUIDField(max_length=255, blank=True, null=True)
    is_Overpayment_Default = models.BooleanField(default=False, blank=False, null=False)

    def save(self, *args, **kwargs):
        if self.is_Overpayment_Default:
            VoteHead.objects.exclude(pk=self.pk).update(is_Overpayment_Default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.vote_head_name
