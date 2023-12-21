from django.db import models

from file_upload.models import SchoolImage
from models import ParentModel
from vouchers.models import Voucher


# Create your models here.
class VoucherAttachment(ParentModel):
    school_id = models.UUIDField(null=True, blank=True, default=None, max_length=255)
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=255)
    fileid = models.ForeignKey(SchoolImage, null=True, default=None, on_delete=models.CASCADE, related_name="voucher_attachments")
    voucher = models.ForeignKey(Voucher, null=True, default=None, on_delete=models.CASCADE, related_name="voucher_attachments")

    def __str__(self):
        return f"{self.id}"



