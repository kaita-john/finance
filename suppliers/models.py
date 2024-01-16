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
    notes = models.CharField(max_length=7000, blank=True, null=True)
    school = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.companyName:
            self.companyName = self.companyName.upper()
        if self.contactPerson:
            self.contactPerson = self.contactPerson.upper()
        if self.phoneNumber:
            self.phoneNumber = self.phoneNumber.upper()
        if self.address:
            self.address = self.address.upper()
        super().save(*args, **kwargs)

    def __str__(self):
        return str(self.id)
