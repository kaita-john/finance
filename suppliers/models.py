from django.db import models

from models import ParentModel


class Supplier(ParentModel):
    companyName = models.CharField(max_length=255, null=True, default=None)
    contactPerson = models.CharField(max_length=255, null=True, default=None)
    phoneNumber = models.CharField(max_length=255, null=True, default=None)
    email = models.CharField(max_length=255, null=True, default=None)
    address = models.CharField(max_length=255, null=True, default=None)
    accountNo = models.CharField(max_length=255, null=True, default=None)
    pinNo = models.CharField(max_length=255, null=True, default=None)
    notes = models.TextField(max_length=255, null=True, default=None)
    school = models.UUIDField(max_length=255, blank=True, null=True)

    def __str__(self):
        return str(self.id)
