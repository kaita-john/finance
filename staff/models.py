from django.db import models

from constants import *
from models import ParentModel


class Staff(ParentModel):
    fname = models.CharField(max_length=255)
    lname = models.CharField(max_length=255)
    staffNo = models.CharField(max_length=255)
    phoneNo = models.CharField(max_length=255)
    gender = models.CharField(max_length=255)
    emailAddress = models.CharField(max_length=255, null=True, blank=True)
    idNumber = models.CharField(max_length=255)
    category = models.CharField(max_length=255, choices=TEACHINGCHOICES, default='TEACHING', )
    school = models.UUIDField(max_length=255, blank=True, null=True)

    def save(self, *args, **kwargs):
        if self.fname:
            self.fname = self.fname.upper()
        if self.lname:
            self.lname = self.lname.upper()
        if self.staffNo:
            self.staffNo = self.staffNo.upper()
        if self.phoneNo:
            self.phoneNo = self.phoneNo.upper()
        if self.gender:
            self.gender = self.gender.upper()
        if self.idNumber:
            self.idNumber = self.idNumber.upper()
        if self.category:
            self.category = self.category.upper()
        super().save(*args, **kwargs)


    def __str__(self):
        return str(self.id)
