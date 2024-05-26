from django.db import models
from django.db.models import DO_NOTHING

from file_upload.models import SchoolImage
from models import ParentModel
from vouchers.models import Voucher


# Create your models here.
class VoucherAttachment(ParentModel):
    school_id = models.UUIDField(null=True, blank=True, default=None, max_length=255)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    fileid = models.ForeignKey(SchoolImage, null=True, default=None, on_delete=DO_NOTHING, related_name="voucher_attachments")
    voucher = models.ForeignKey(Voucher, null=True, default=None, on_delete=models.SET_NULL, related_name="attachments")

    def save(self, *args, **kwargs):
        if self.name:
            self.name = self.name.upper()
        if self.type:
            self.type = self.type.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id}"



